#!/usr/bin/env python3
# ml/src/pipeline/daily_pipeline.py

"""
日次パイプライン

毎営業日実行する処理:
1. 日次データ取得（yfinance）
2. 推論実行（ONNX Runtime）
3. 結果をS3にアップロード（オプション）

使用例:
    # 設定ファイルを指定して実行
    python src/pipeline/daily_pipeline.py \
      --fetch-config config/fetch_daily_universe.yaml \
      --predict-config config/predict.yaml

    # データ取得をスキップ（推論のみ）
    python src/pipeline/daily_pipeline.py \
      --predict-config config/predict.yaml \
      --skip-fetch
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from common.logging_config import setup_logger
from common.error_handler import validate_file_exists

logger = setup_logger(__name__)


def run_daily_data_fetch(config_path: Path) -> bool:
    """
    日次データ取得を実行

    Args:
        config_path: 設定ファイルパス

    Returns:
        bool: 成功した場合True
    """
    from data.fetch_daily_universe import main as fetch_main

    logger.info("Step 1/2: Fetching daily data...")
    logger.info(f"  Config: {config_path}")

    # 引数を構築
    args = ["--config", str(config_path)]

    # 既存のargvを保存
    original_argv = sys.argv
    try:
        sys.argv = ["fetch_daily_universe.py"] + args
        fetch_main()
        logger.info("✓ Daily data fetch completed")
        return True
    except Exception as e:
        logger.error(f"✗ Daily data fetch failed: {e}")
        return False
    finally:
        sys.argv = original_argv


def run_daily_inference(config_path: Path) -> bool:
    """
    日次推論を実行

    Args:
        config_path: 設定ファイルパス

    Returns:
        bool: 成功した場合True
    """
    from inference.predict import main as predict_main

    logger.info("Step 2/2: Running inference...")
    logger.info(f"  Config: {config_path}")

    # 引数を構築
    args = ["--config", str(config_path)]

    # 既存のargvを保存
    original_argv = sys.argv
    try:
        sys.argv = ["predict.py"] + args
        predict_main()
        logger.info("✓ Inference completed")
        return True
    except Exception as e:
        logger.error(f"✗ Inference failed: {e}")
        return False
    finally:
        sys.argv = original_argv


def main():
    """日次パイプラインのメイン処理"""
    parser = argparse.ArgumentParser(
        description="Daily pipeline: data fetch + inference",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 設定ファイルを指定して実行
  python src/pipeline/daily_pipeline.py \\
    --fetch-config config/fetch_daily_universe.yaml \\
    --predict-config config/predict.yaml

  # データ取得をスキップ（推論のみ）
  python src/pipeline/daily_pipeline.py \\
    --predict-config config/predict.yaml \\
    --skip-fetch

  # 環境変数を使用
  FETCH_CONFIG=config/fetch_daily_universe.yaml \\
  PREDICT_CONFIG=config/predict.yaml \\
  python src/pipeline/daily_pipeline.py
        """,
    )

    # 設定ファイル引数
    parser.add_argument(
        "--fetch-config",
        type=str,
        default=os.getenv("FETCH_CONFIG", "config/fetch_daily_universe.yaml"),
        help="Path to fetch config yaml file (環境変数: FETCH_CONFIG)",
    )
    parser.add_argument(
        "--predict-config",
        type=str,
        default=os.getenv("PREDICT_CONFIG", "config/predict.yaml"),
        help="Path to predict config yaml file (環境変数: PREDICT_CONFIG)",
    )

    # オプション
    parser.add_argument(
        "--skip-fetch",
        action="store_true",
        help="Skip data fetch step (use existing data)",
    )

    args = parser.parse_args()

    # パスを解決
    fetch_config = Path(args.fetch_config)
    predict_config = Path(args.predict_config)

    # ファイル存在確認
    if not args.skip_fetch:
        try:
            validate_file_exists(fetch_config, "Fetch config")
        except FileNotFoundError as e:
            logger.error(str(e))
            sys.exit(1)

    try:
        validate_file_exists(predict_config, "Predict config")
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    # パイプライン開始
    start_time = datetime.now()
    logger.info("=" * 80)
    logger.info("Daily Pipeline Started")
    logger.info("=" * 80)
    logger.info(f"Timestamp: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Fetch Config: {fetch_config}")
    logger.info(f"Predict Config: {predict_config}")
    logger.info(f"Skip Fetch: {args.skip_fetch}")
    logger.info("=" * 80)

    success = True

    # Step 1: 日次データ取得
    if not args.skip_fetch:
        fetch_success = run_daily_data_fetch(fetch_config)
        if not fetch_success:
            logger.error("Pipeline failed at data fetch step")
            success = False
    else:
        logger.info("Step 1/2: Skipping data fetch (using existing data)")

    # Step 2: 推論実行
    if success or args.skip_fetch:
        inference_success = run_daily_inference(predict_config)
        if not inference_success:
            logger.error("Pipeline failed at inference step")
            success = False

    # 完了
    end_time = datetime.now()
    elapsed = end_time - start_time

    logger.info("=" * 80)
    if success:
        logger.info("Daily Pipeline Completed Successfully!")
    else:
        logger.info("Daily Pipeline Failed")
    logger.info(f"Elapsed time: {elapsed}")
    logger.info("=" * 80)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
