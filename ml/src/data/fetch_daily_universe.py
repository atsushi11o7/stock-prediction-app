# ml/src/data/fetch_daily_universe.py

"""
Daily market data fetcher for stock universe

営業日の終わりに実行し、当日のOHLCVデータを取得してJSON形式で保存する。
ローカルファイルシステムまたはS3に出力可能。
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone, date
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import yaml

# Add parent directory to path to allow imports
import sys
script_dir = Path(__file__).resolve().parent.parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

from common.logging_config import setup_logger
from data.utils.config import (
    RetryConfig,
    load_yaml,
    parse_as_of,
    resolve_universe_yaml_path,
    resolve_universe_yaml_path_with_s3,
    get_base_dir,
    get_env_config,
    resolve_path,
)
from data.utils.universe_loader import get_tickers_from_universe_yaml
from data.utils.io import write_daily_payloads
from data.utils.s3io import put_json
from data.utils.yfin import safe_history, select_row_for_asof, map_row_fields

logger = setup_logger(__name__)


def fetch_daily_data(
    tickers: List[str],
    as_of_d: Optional[date],
    period: str,
    interval: str,
    use_adj: bool,
    fields: List[str],
    retry: RetryConfig,
) -> tuple[List[Dict[str, Any]], date]:
    """
    複数銘柄の日次データを取得する

    Args:
        tickers: ティッカーリスト
        as_of_d: 取得対象日（Noneの場合は最新）
        period: yfinanceのperiodパラメータ
        interval: yfinanceのintervalパラメータ
        use_adj: 調整後終値を使用するか
        fields: 取得するフィールドリスト
        retry: リトライ設定

    Returns:
        (records, chosen_as_of): 取得したレコードリストと実際の取得日

    Raises:
        ValueError: データが1件も取得できなかった場合
    """
    records: List[Dict[str, Any]] = []
    chosen_as_of: Optional[date] = None
    failed_tickers: List[str] = []

    for idx, tk in enumerate(tickers, 1):
        print(f"[{idx}/{len(tickers)}] Fetching {tk}...", end=" ")

        try:
            df = safe_history(tk, period, interval, retry.times, retry.sleep_seconds)
            row = select_row_for_asof(df, as_of_d)

            if row is None:
                print(f"NO DATA (as_of={as_of_d or 'auto'})")
                failed_tickers.append(tk)
                continue

            # 実際の取得日を記録
            rd = pd.to_datetime(row.name).tz_localize(None).date()
            if chosen_as_of is None or rd > chosen_as_of:
                chosen_as_of = rd

            item = {"ticker": tk}
            item.update(map_row_fields(row, use_adj, fields))
            records.append(item)

            print(f"OK (date={rd})")

        except Exception as e:
            print(f"ERROR: {e}")
            failed_tickers.append(tk)

    if not records:
        raise ValueError(
            f"No records collected. All {len(tickers)} tickers failed. "
            f"Failed tickers: {', '.join(failed_tickers)}"
        )

    if failed_tickers:
        print(f"\n[WARNING] Failed to fetch {len(failed_tickers)}/{len(tickers)} tickers:")
        for tk in failed_tickers:
            print(f"  - {tk}")

    # 最終的な日付を決定
    final_date = chosen_as_of or (as_of_d or datetime.now(timezone.utc).date())

    return records, final_date


def save_output(
    payload: Dict[str, Any],
    day_str: str,
    cfg: Dict[str, Any],
    base_dir: Path,
) -> None:
    """
    データを保存する（ローカル/S3）

    Args:
        payload: 保存するJSONペイロード
        day_str: 日付文字列（YYYY-MM-DD）
        cfg: 全体設定
        base_dir: ベースディレクトリ（ml/）
    """
    env = cfg.get("env", "local")
    env_cfg = cfg.get(env, {})
    output_cfg = env_cfg.get("output", {})

    if env == "local":
        outdir = Path(output_cfg.get("dir", "data/serving/daily"))
        if not outdir.is_absolute():
            outdir = base_dir / outdir
        outdir = outdir.resolve()

        write_daily_payloads(outdir, day_str, payload)
        print(f"[OK] Local saved: {outdir / f'{day_str}.json'}")
        print(f"[OK] Latest link: {outdir / 'latest.json'}")

    elif env == "s3":
        s3_cfg = cfg.get("s3", {})
        bucket = str(s3_cfg["bucket"])
        daily_prefix = str(output_cfg.get("daily_prefix", "market_data/serving/daily"))

        # 日付別ファイル
        key = f"{daily_prefix}/{day_str}.json"
        put_json(bucket=bucket, key=key, payload=payload)
        print(f"[OK] S3 uploaded: s3://{bucket}/{key}")

        # latest.json
        latest_key = f"{daily_prefix}/latest.json"
        put_json(bucket=bucket, key=latest_key, payload=payload)
        print(f"[OK] S3 uploaded: s3://{bucket}/{latest_key}")


def parse_args() -> argparse.Namespace:
    """コマンドライン引数をパースする"""
    parser = argparse.ArgumentParser(
        description="Fetch daily market data for a stock universe and save as JSON (local/S3).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 設定ファイルを指定して実行
  python fetch_daily_universe.py --config ml/config/fetch_daily_universe.yaml

  # 環境変数を使用
  CONFIG_PATH=ml/config/fetch_daily_universe.yaml python fetch_daily_universe.py
""",
    )

    parser.add_argument(
        "--config",
        type=str,
        default=os.environ.get("CONFIG_PATH"),
        help="Path to config yaml file (環境変数: CONFIG_PATH)",
    )

    args = parser.parse_args()

    if not args.config:
        parser.error("--config is required (or set CONFIG_PATH environment variable)")

    return args


def main() -> None:
    """メイン関数"""
    try:
        args = parse_args()
        config_path = Path(args.config).resolve()

        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        cfg: Dict[str, Any] = load_yaml(config_path)
        base_dir = config_path.parent.parent  # ml/ ディレクトリ

        env = cfg.get("env", "local")

        print("=" * 60)
        print("Daily Market Data Fetcher")
        print("=" * 60)
        print(f"\nConfig file: {config_path}")
        print(f"Environment: {env}")
        print("=" * 60)

        # Universe tickers（環境に応じてローカルまたはS3から取得）
        universe_yaml = resolve_universe_yaml_path_with_s3(cfg, config_path)
        print(f"\n[INFO] Loading universe from: {universe_yaml}")
        tickers = get_tickers_from_universe_yaml(universe_yaml)

        if not tickers:
            raise ValueError("No tickers found in universe file")

        print(f"[INFO] Found {len(tickers)} tickers\n")

        # Parameters
        as_of_d = parse_as_of(str(cfg.get("as_of", "auto")))

        yf_cfg = cfg.get("yf", {}) or {}
        interval = str(yf_cfg.get("interval", "1d"))
        period = str(yf_cfg.get("period", "3d"))
        use_adj = bool(yf_cfg.get("use_adjclose", True))

        fields = list(cfg.get("fields", ["open", "high", "low", "close", "adjclose", "volume"]))

        retry_cfg = cfg.get("retry", {}) or {}
        retry = RetryConfig(
            times=int(retry_cfg.get("times", 3)),
            sleep_seconds=float(retry_cfg.get("sleep_seconds", 1.0)),
        )

        print(f"[INFO] Fetch parameters:")
        print(f"  as_of: {as_of_d or 'auto (latest)'}")
        print(f"  period: {period}, interval: {interval}")
        print(f"  use_adjclose: {use_adj}")
        print(f"  fields: {', '.join(fields)}")
        print(f"  retry: {retry.times} times, sleep: {retry.sleep_seconds}s\n")

        # Fetch data
        print("[INFO] Fetching data...")
        records, final_date = fetch_daily_data(
            tickers=tickers,
            as_of_d=as_of_d,
            period=period,
            interval=interval,
            use_adj=use_adj,
            fields=fields,
            retry=retry,
        )

        day_str = final_date.isoformat()
        payload = {
            "as_of": day_str,
            "count": len(records),
            "symbols": records,
        }

        print(f"\n[SUCCESS] Collected {len(records)} records for {day_str}")

        # Save output
        print("\n[INFO] Saving output...")
        save_output(payload, day_str, cfg, base_dir)

        print("\n" + "=" * 60)
        print("[SUCCESS] Daily data fetch completed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
