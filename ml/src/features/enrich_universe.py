# src/features/enrich_universe.py

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional
import yaml
import yfinance as yf

# Add parent directory to path
script_dir = Path(__file__).resolve().parent.parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

from common.logging_config import setup_logger
from data.utils.config import load_config, get_base_dir, resolve_path

logger = setup_logger(__name__)


def fetch_ticker_info(ticker: str) -> Dict[str, Any]:
    """
    yfinanceから銘柄情報を取得する

    Args:
        ticker: ティッカーシンボル（例: "6501.T"）

    Returns:
        info辞書（取得失敗時は空辞書）
    """
    try:
        tk = yf.Ticker(ticker)
        try:
            info = tk.get_info()
        except Exception:
            info = tk.info
        return info or {}
    except Exception as e:
        logger.warning(f"Failed to fetch info for {ticker}: {e}")
        return {}


def extract_static_features(info: Dict[str, Any]) -> Dict[str, Optional[Any]]:
    """
    yfinanceのinfo辞書から静的特徴量を抽出する

    Args:
        info: yfinanceから取得したinfo辞書

    Returns:
        静的特徴量の辞書（sector, industry, PER, PBR, DividendYield）
    """
    return {
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "PER": info.get("trailingPE"),
        "PBR": info.get("priceToBook"),
        "DividendYield": info.get("dividendYield"),
    }


def enrich_universe(
    input_path: str,
    output_path: str,
    update_mode: str = "full",
) -> None:
    """
    銘柄ユニバース（universe）に対して yfinance から静的情報を取得し、
    付与した YAML を保存する

    Args:
        input_path: 入力YAMLファイルパス
        output_path: 出力YAMLファイルパス
        update_mode: 更新モード ("full" or "valuation-only")

    取得する情報:
    - sector: セクター（例: "Industrials"）
    - industry: 業種（例: "Conglomerates"）
    - PER: 株価収益率（trailingPE）
    - PBR: 株価純資産倍率（priceToBook）
    - DividendYield: 配当利回り（dividendYield）

    入力 YAML 形式:
    universe:
      - code: 6501
        name: 日立製作所
        ticker: "6501.T"

    出力 YAML 形式:
    universe:
      - code: 6501
        name: 日立製作所
        ticker: "6501.T"
        sector: Industrials
        industry: Conglomerates
        PER: 12.34
        PBR: 1.23
        DividendYield: 0.0234
    """
    print("=" * 60)
    print("Universe Enrichment with yfinance Static Features")
    print("=" * 60)
    print(f"\nMode: {update_mode}")
    print(f"Input:  {input_path}")
    print(f"Output: {output_path}\n")

    input_path_obj = Path(input_path)
    output_path_obj = Path(output_path)

    if not input_path_obj.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    print(f"[INFO] Loading universe from: {input_path}")
    cfg_in = yaml.safe_load(input_path_obj.read_text(encoding="utf-8")) or {}

    universe = cfg_in.get("universe", [])
    if not universe:
        raise ValueError("No universe data found in input file")

    print(f"[INFO] Found {len(universe)} tickers to enrich\n")

    valuation_only = update_mode == "valuation-only"

    updated_universe = []

    for idx, item in enumerate(universe, 1):
        ticker = item.get("ticker")
        if not ticker:
            print(f"[WARNING] Skipping item {idx}: no ticker field")
            continue

        print(f"[{idx}/{len(universe)}] Fetching info for {ticker} ({item.get('name', 'N/A')}) ...")

        info = fetch_ticker_info(ticker)
        features = extract_static_features(info)

        # valuation-onlyモードの場合、sector/industryは既存値を保持
        if valuation_only:
            enriched_item = {**item}
            enriched_item["PER"] = features["PER"]
            enriched_item["PBR"] = features["PBR"]
            enriched_item["DividendYield"] = features["DividendYield"]
        else:
            # fullモード: すべてのフィールドを更新
            enriched_item = {**item, **features}

        # 取得した情報を表示
        if valuation_only:
            print(f"  PER={features['PER']}")
            print(f"  PBR={features['PBR']}")
            print(f"  DividendYield={features['DividendYield']}")
        else:
            print(f"  sector={features['sector']}")
            print(f"  industry={features['industry']}")
            print(f"  PER={features['PER']}")
            print(f"  PBR={features['PBR']}")
            print(f"  DividendYield={features['DividendYield']}")
        print()

        updated_universe.append(enriched_item)

    out_cfg = {
        "universe": updated_universe,
    }

    # 出力ディレクトリが存在しない場合は作成
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] Saving enriched universe → {output_path}")
    output_path_obj.write_text(
        yaml.safe_dump(
            out_cfg,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
        ),
        encoding="utf-8",
    )

    print("\n" + "=" * 60)
    print("[SUCCESS] Universe enrichment completed!")
    print(f"[INFO] Output saved to: {output_path}")
    print("=" * 60)


def parse_args() -> argparse.Namespace:
    """コマンドライン引数をパースする"""
    parser = argparse.ArgumentParser(
        description="銘柄ユニバースにyfinanceから静的情報を付与する",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 設定ファイルを使用（推奨）
  python enrich_universe.py --config config/enrich_universe.yaml

  # 直接引数を指定
  python enrich_universe.py \\
    --input config/universes/topix_core_30_20251031.yaml \\
    --output config/universes/enrich_topix_core_30_20251031.yaml

  # 月次更新（バリュエーション指標のみ）
  python enrich_universe.py \\
    --config config/enrich_universe.yaml \\
    --update-mode valuation-only
""",
    )

    parser.add_argument(
        "--config",
        type=str,
        default=os.environ.get("ENRICH_CONFIG"),
        help="設定ファイルパス（環境変数: ENRICH_CONFIG）",
    )

    parser.add_argument(
        "--input",
        type=str,
        default=os.environ.get("INPUT_PATH"),
        help="入力YAMLファイルパス（環境変数: INPUT_PATH）",
    )

    parser.add_argument(
        "--output",
        type=str,
        default=os.environ.get("OUTPUT_PATH"),
        help="出力YAMLファイルパス（環境変数: OUTPUT_PATH）",
    )

    parser.add_argument(
        "--update-mode",
        type=str,
        choices=["full", "valuation-only"],
        default=os.environ.get("UPDATE_MODE", "full"),
        help=(
            "更新モード（環境変数: UPDATE_MODE）\n"
            "  full: すべての情報を取得（sector, industry, PER, PBR, DividendYield）\n"
            "  valuation-only: バリュエーション指標のみ更新（PER, PBR, DividendYield）"
        ),
    )

    return parser.parse_args()


def main() -> None:
    """メイン関数"""
    try:
        args = parse_args()

        # 設定ファイルが指定された場合は読み込み
        if args.config:
            config_path = Path(args.config)
            if not config_path.is_absolute():
                config_path = Path(__file__).resolve().parent.parent.parent / config_path
            cfg = load_config(config_path)
            base_dir = get_base_dir(config_path)

            input_path = args.input or cfg.get("input_path")
            output_path = args.output or cfg.get("output_path")
            update_mode = cfg.get("update_mode", args.update_mode)

            # 相対パスをbase_dirから解決
            if input_path and not Path(input_path).is_absolute():
                input_path = str(resolve_path(input_path, base_dir))
            if output_path and not Path(output_path).is_absolute():
                output_path = str(resolve_path(output_path, base_dir))
        else:
            input_path = args.input
            output_path = args.output
            update_mode = args.update_mode

        # 必須パラメータのチェック
        if not input_path:
            raise ValueError("--input or config.input_path is required")
        if not output_path:
            raise ValueError("--output or config.output_path is required")

        enrich_universe(
            input_path=input_path,
            output_path=output_path,
            update_mode=update_mode,
        )
    except Exception as e:
        print(f"\n[ERROR] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
