# ml/src/data/fetch_daily_backfill.py

"""
Historical daily market data backfill for stock universe

初回実行時または過去データの補充時に使用。
指定した期間の日次データを取得し、日付ごとのJSON形式で保存する。
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import yaml

# Add parent directory to path to allow imports
script_dir = Path(__file__).resolve().parent.parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

from common.logging_config import setup_logger
from data.utils.config import (
    RetryConfig,
    load_yaml,
    resolve_universe_yaml_path,
)
from data.utils.universe_loader import get_tickers_from_universe_yaml
from data.utils.io import ensure_dir, write_json
from data.utils.s3io import put_json
from data.utils.yfin import safe_history
from data.utils.aggregate import build_by_date

logger = setup_logger(__name__)


def fetch_historical_data(
    tickers: List[str],
    period: str,
    interval: str,
    use_adj: bool,
    fields: List[str],
    retry: RetryConfig,
) -> tuple[Dict[str, List[Dict[str, Any]]], Optional[pd.Timestamp]]:
    """
    複数銘柄の履歴データを取得し、日付ごとに集約する

    Args:
        tickers: ティッカーリスト
        period: yfinanceのperiodパラメータ（例: "5y"）
        interval: yfinanceのintervalパラメータ（例: "1d"）
        use_adj: 調整後終値を使用するか
        fields: 取得するフィールドリスト
        retry: リトライ設定

    Returns:
        (by_date, latest_dt): 日付ごとのデータ辞書と最新日時

    Raises:
        ValueError: データが1件も取得できなかった場合
    """
    by_date: Dict[str, List[Dict[str, Any]]] = {}
    latest_dt: Optional[pd.Timestamp] = None
    failed_tickers: List[str] = []

    for idx, tk in enumerate(tickers, 1):
        print(f"[{idx}/{len(tickers)}] Fetching {tk} (period={period})...", end=" ")

        try:
            df = safe_history(tk, period, interval, retry.times, retry.sleep_seconds)

            if df.empty:
                print("NO DATA")
                failed_tickers.append(tk)
                continue

            ticker_by_date, ticker_latest = build_by_date(tk, df, use_adj, fields)

            # マージ
            for day_str, records in ticker_by_date.items():
                by_date.setdefault(day_str, []).extend(records)

            if latest_dt is None or (ticker_latest is not None and ticker_latest > latest_dt):
                latest_dt = ticker_latest

            print(f"OK ({len(ticker_by_date)} days)")

        except Exception as e:
            print(f"ERROR: {e}")
            failed_tickers.append(tk)

    if not by_date:
        raise ValueError(
            f"No data collected. All {len(tickers)} tickers failed. "
            f"Failed tickers: {', '.join(failed_tickers)}"
        )

    if failed_tickers:
        print(f"\n[WARNING] Failed to fetch {len(failed_tickers)}/{len(tickers)} tickers:")
        for tk in failed_tickers:
            print(f"  - {tk}")

    return by_date, latest_dt


def save_backfill_output(
    by_date: Dict[str, List[Dict[str, Any]]],
    cfg: Dict[str, Any],
    base_dir: Path,
) -> None:
    """
    バックフィルデータを保存する（ローカル/S3）

    Args:
        by_date: 日付ごとのデータ辞書
        cfg: 全体設定
        base_dir: ベースディレクトリ（ml/）
    """
    sorted_dates = sorted(by_date.keys())

    env = cfg.get("env", "local")
    env_cfg = cfg.get(env, {})
    output_cfg = env_cfg.get("output", {})

    if env == "local":
        outdir = Path(output_cfg.get("dir", "data/training/daily"))
        if not outdir.is_absolute():
            outdir = base_dir / outdir
        outdir = outdir.resolve()
        ensure_dir(outdir)

        print(f"\n[INFO] Saving to local directory: {outdir}")
        for idx, day_str in enumerate(sorted_dates, 1):
            symbols = by_date[day_str]
            payload = {
                "as_of": day_str,
                "count": len(symbols),
                "symbols": symbols,
            }
            write_json(outdir / f"{day_str}.json", payload)

            if idx % 100 == 0 or idx == len(sorted_dates):
                print(f"  Progress: {idx}/{len(sorted_dates)} files written")

        # latest.json
        latest_day = sorted_dates[-1]
        latest_payload = {
            "as_of": latest_day,
            "count": len(by_date[latest_day]),
            "symbols": by_date[latest_day],
        }
        write_json(outdir / "latest.json", latest_payload)

        print(f"[OK] Local saved: {len(sorted_dates)} files")
        print(f"[OK] Latest: {outdir / 'latest.json'} ({latest_day})")

    elif env == "s3":
        s3_cfg = cfg.get("s3", {})
        bucket = str(s3_cfg["bucket"])
        daily_prefix = str(output_cfg.get("daily_prefix", "market_data/training/daily"))

        print(f"\n[INFO] Uploading to S3: s3://{bucket}/{daily_prefix}")
        for idx, day_str in enumerate(sorted_dates, 1):
            symbols = by_date[day_str]
            payload = {
                "as_of": day_str,
                "count": len(symbols),
                "symbols": symbols,
            }

            key = f"{daily_prefix}/{day_str}.json"
            put_json(bucket=bucket, key=key, payload=payload)

            if idx % 100 == 0 or idx == len(sorted_dates):
                print(f"  Progress: {idx}/{len(sorted_dates)} files uploaded")

        # latest.json
        latest_day = sorted_dates[-1]
        latest_payload = {
            "as_of": latest_day,
            "count": len(by_date[latest_day]),
            "symbols": by_date[latest_day],
        }
        latest_key = f"{daily_prefix}/latest.json"
        put_json(bucket=bucket, key=latest_key, payload=latest_payload)

        print(f"[OK] S3 uploaded: {len(sorted_dates)} files")
        print(f"[OK] Latest: s3://{bucket}/{latest_key} ({latest_day})")


def parse_args() -> argparse.Namespace:
    """コマンドライン引数をパースする"""
    parser = argparse.ArgumentParser(
        description="Backfill historical daily market data for a stock universe and save as JSON (local/S3).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 設定ファイルを指定して実行
  python fetch_daily_backfill.py --config ml/config/fetch_daily_backfill.yaml

  # 環境変数を使用
  CONFIG_PATH=ml/config/fetch_daily_backfill.yaml python fetch_daily_backfill.py
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
        print("Daily Market Data Backfill")
        print("=" * 60)
        print(f"\nConfig file: {config_path}")
        print(f"Environment: {env}")
        print("=" * 60)

        # Universe tickers
        universe_yaml = resolve_universe_yaml_path(cfg, config_path)
        print(f"\n[INFO] Loading universe from: {universe_yaml}")
        tickers = get_tickers_from_universe_yaml(universe_yaml)

        if not tickers:
            raise ValueError("No tickers found in universe file")

        print(f"[INFO] Found {len(tickers)} tickers\n")

        # Parameters
        yf_cfg = cfg.get("yf", {}) or {}
        interval = str(yf_cfg.get("interval", "1d"))
        period = str(yf_cfg.get("period", "5y"))
        use_adj = bool(yf_cfg.get("use_adjclose", True))

        fields = list(cfg.get("fields", ["open", "high", "low", "close", "adjclose", "volume"]))

        retry_cfg = cfg.get("retry", {}) or {}
        retry = RetryConfig(
            times=int(retry_cfg.get("times", 3)),
            sleep_seconds=float(retry_cfg.get("sleep_seconds", 1.0)),
        )

        print(f"[INFO] Backfill parameters:")
        print(f"  period: {period}, interval: {interval}")
        print(f"  use_adjclose: {use_adj}")
        print(f"  fields: {', '.join(fields)}")
        print(f"  retry: {retry.times} times, sleep: {retry.sleep_seconds}s\n")

        # Fetch historical data
        print("[INFO] Fetching historical data...")
        by_date, latest_dt = fetch_historical_data(
            tickers=tickers,
            period=period,
            interval=interval,
            use_adj=use_adj,
            fields=fields,
            retry=retry,
        )

        total_records = sum(len(v) for v in by_date.values())
        date_range = f"{min(by_date.keys())} to {max(by_date.keys())}"

        print(f"\n[SUCCESS] Collected {total_records} records across {len(by_date)} days")
        print(f"[INFO] Date range: {date_range}")

        # Save output
        save_backfill_output(by_date, cfg, base_dir)

        print("\n" + "=" * 60)
        print("[SUCCESS] Daily data backfill completed!")
        print(f"[INFO] Total: {total_records} records, {len(by_date)} days")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
