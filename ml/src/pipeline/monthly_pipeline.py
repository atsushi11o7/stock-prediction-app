#!/usr/bin/env python3
# ml/src/pipeline/monthly_pipeline.py

"""
月次パイプライン

毎月1日に実行する処理:
1. 静的特徴量の更新（PER, PBR, 配当利回り）
2. ファインチューニング実行
3. 新しいONNXモデルをS3にアップロード

使用例:
    # 設定ファイルを指定して実行
    python src/pipeline/monthly_pipeline.py \
      --enrich-config config/enrich_universe.yaml \
      --finetune-config config/finetune.yaml

    # エンリッチメントをスキップ
    python src/pipeline/monthly_pipeline.py \
      --finetune-config config/finetune.yaml \
      --skip-enrich

    # 環境変数を使用
    ENRICH_CONFIG=config/enrich_universe.yaml \
    FINETUNE_CONFIG=config/finetune.yaml \
    python src/pipeline/monthly_pipeline.py
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from common.logging_config import setup_logger
from common.error_handler import validate_file_exists

logger = setup_logger(__name__)


def run_enrich_universe(config_path: Path) -> bool:
    """
    Universe YAMLに静的特徴量を付与

    Args:
        config_path: 設定ファイルパス

    Returns:
        bool: 成功した場合True
    """
    from features.enrich_universe import main as enrich_main

    logger.info("Step 1/2: Enriching universe with static features...")
    logger.info(f"  Config: {config_path}")

    # 引数を構築
    args = ["--config", str(config_path)]

    # 既存のargvを保存
    original_argv = sys.argv
    try:
        # enrich_universe.pyの引数として設定
        sys.argv = ["enrich_universe.py"] + args
        enrich_main()
        logger.info("✓ Universe enrichment completed")
        return True
    except Exception as e:
        logger.error(f"✗ Universe enrichment failed: {e}")
        return False
    finally:
        # argvを復元
        sys.argv = original_argv


def run_finetuning(config_path: Path) -> bool:
    """
    ファインチューニングを実行

    Args:
        config_path: 設定ファイルパス

    Returns:
        bool: 成功した場合True
    """
    from training.finetune import main as finetune_main

    logger.info("Step 2/2: Running finetuning...")
    logger.info(f"  Config: {config_path}")

    # 引数を構築
    args = ["--config", str(config_path)]

    # 既存のargvを保存
    original_argv = sys.argv
    try:
        # finetune.pyの引数として設定
        sys.argv = ["finetune.py"] + args
        finetune_main()
        logger.info("✓ Finetuning completed")
        return True
    except Exception as e:
        logger.error(f"✗ Finetuning failed: {e}")
        return False
    finally:
        # argvを復元
        sys.argv = original_argv


def main():
    """月次パイプラインのメイン処理"""
    parser = argparse.ArgumentParser(
        description="Monthly pipeline: enrich universe + finetuning",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 設定ファイルを指定して実行
  python src/pipeline/monthly_pipeline.py \\
    --enrich-config config/enrich_universe.yaml \\
    --finetune-config config/finetune.yaml

  # エンリッチメントをスキップ
  python src/pipeline/monthly_pipeline.py \\
    --finetune-config config/finetune.yaml \\
    --skip-enrich

  # 環境変数を使用
  ENRICH_CONFIG=config/enrich_universe.yaml \\
  FINETUNE_CONFIG=config/finetune.yaml \\
  python src/pipeline/monthly_pipeline.py
        """,
    )

    # 設定ファイル引数
    parser.add_argument(
        "--enrich-config",
        type=str,
        default=os.getenv("ENRICH_CONFIG", "config/enrich_universe.yaml"),
        help="Path to enrich config yaml file (環境変数: ENRICH_CONFIG)",
    )
    parser.add_argument(
        "--finetune-config",
        type=str,
        default=os.getenv("FINETUNE_CONFIG", "config/finetune.yaml"),
        help="Path to finetune config yaml file (環境変数: FINETUNE_CONFIG)",
    )

    # オプション
    parser.add_argument(
        "--skip-enrich",
        action="store_true",
        help="Skip universe enrichment step (use existing enriched YAML)",
    )

    args = parser.parse_args()

    # パスを解決
    enrich_config = Path(args.enrich_config)
    finetune_config = Path(args.finetune_config)

    # ファイル存在確認
    if not args.skip_enrich:
        try:
            validate_file_exists(enrich_config, "Enrich config")
        except FileNotFoundError as e:
            logger.error(str(e))
            sys.exit(1)

    try:
        validate_file_exists(finetune_config, "Finetune config")
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    # パイプライン開始
    start_time = datetime.now()
    logger.info("=" * 80)
    logger.info("Monthly Pipeline Started")
    logger.info("=" * 80)
    logger.info(f"Timestamp: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Enrich Config: {enrich_config}")
    logger.info(f"Finetune Config: {finetune_config}")
    logger.info(f"Skip Enrich: {args.skip_enrich}")
    logger.info("=" * 80)

    success = True

    # Step 1: Universe enrichment
    if not args.skip_enrich:
        enrich_success = run_enrich_universe(enrich_config)
        if not enrich_success:
            logger.error("Pipeline failed at universe enrichment step")
            success = False
    else:
        logger.info("Step 1/2: Skipping universe enrichment (using existing enriched YAML)")

    # Step 2: Finetuning
    if success or args.skip_enrich:
        finetune_success = run_finetuning(finetune_config)
        if not finetune_success:
            logger.error("Pipeline failed at finetuning step")
            success = False

    # パイプライン終了
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    logger.info("=" * 80)
    if success:
        logger.info("✓ Monthly Pipeline Completed Successfully")
    else:
        logger.error("✗ Monthly Pipeline Failed")
    logger.info(f"Duration: {duration:.1f} seconds ({duration / 60:.1f} minutes)")
    logger.info("=" * 80)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
