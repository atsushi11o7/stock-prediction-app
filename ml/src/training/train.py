#!/usr/bin/env python3
# ml/src/training/train.py

"""
株価予測モデル学習スクリプト

設定ファイルを読み込み、モデルの学習・検証・テスト・ONNXエクスポートを実行する。
ローカル保存とS3保存の両方に対応。
"""

from __future__ import annotations
import argparse
import os
import sys
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

import torch
import pytorch_lightning as pl
from pytorch_lightning.callbacks import (
    ModelCheckpoint,
    EarlyStopping,
    LearningRateMonitor,
)
from pytorch_lightning.loggers import TensorBoardLogger, CSVLogger

# パスの設定
script_dir = Path(__file__).resolve().parent.parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

from common.logging_config import setup_logger
from common.s3_operations import upload_onnx_to_s3
from data.utils.config import load_config, get_base_dir, get_env_config, resolve_path
from model_src.datamodules.lstm_datamodule import LSTMDataModule
from model_src.lit_modules.lit_model import StockPredictionLitModule
from features.weekly_features import get_weekly_feature_columns
from features.valuation_features import get_static_feature_columns
from training.utils.onnx_export import export_to_onnx, verify_onnx_model, save_model_metadata

logger = setup_logger(__name__)


def setup_seed(seed: int, deterministic: bool = True) -> None:
    """
    乱数シードの設定

    Args:
        seed: シード値
        deterministic: 決定的な動作にするか
    """
    pl.seed_everything(seed, workers=True)

    if deterministic:
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


def setup_directories(config: Dict[str, Any], config_path: Path) -> Dict[str, Path]:
    """
    出力ディレクトリの作成

    Args:
        config: 設定辞書
        config_path: 設定ファイルのパス

    Returns:
        dirs: ディレクトリパスの辞書
    """
    env, _, _, output_cfg = get_env_config(config)
    base_dir = get_base_dir(config_path)
    dirs = {}

    if env == "local":
        dirs["checkpoint"] = resolve_path(output_cfg.get("checkpoint_dir", "checkpoints"), base_dir)
        dirs["onnx"] = resolve_path(output_cfg.get("onnx_dir", "models/onnx"), base_dir)
        dirs["logs"] = resolve_path(output_cfg.get("logs_dir", "logs"), base_dir)

        for d in dirs.values():
            d.mkdir(parents=True, exist_ok=True)
    else:
        # S3環境の場合は一時ディレクトリを使用
        import tempfile
        tmp_dir = Path(tempfile.mkdtemp(prefix="train_"))
        dirs["checkpoint"] = tmp_dir / "checkpoints"
        dirs["onnx"] = tmp_dir / "onnx"
        dirs["logs"] = tmp_dir / "logs"
        for d in dirs.values():
            d.mkdir(parents=True, exist_ok=True)

    return dirs


def create_datamodule(config: Dict[str, Any], config_path: Path) -> LSTMDataModule:
    """
    DataModuleを作成

    Args:
        config: 設定辞書
        config_path: 設定ファイルのパス

    Returns:
        datamodule: LSTMDataModule
    """
    from data.utils.config import resolve_universe_yaml_path_with_s3

    data_cfg = config.get("data", {})
    base_dir = get_base_dir(config_path)
    env, _, input_cfg, _ = get_env_config(config)

    if env == "s3":
        raise NotImplementedError("S3 data loading for training is not yet implemented")

    daily_data_dir = resolve_path(input_cfg.get("daily_data_dir", "data/training/daily"), base_dir)

    # universeファイルパスの解決（環境に応じてローカルまたはS3から取得）
    universe_yaml_path = resolve_universe_yaml_path_with_s3(config, config_path)

    # features_csv_dirの解決
    features_csv_dir = data_cfg.get("features_csv_dir")
    if features_csv_dir:
        features_csv_dir = str(resolve_path(features_csv_dir, base_dir))

    datamodule = LSTMDataModule(
        daily_data_dir=str(daily_data_dir),
        universe_yaml_path=str(universe_yaml_path),
        batch_size=data_cfg.get("batch_size", 32),
        num_workers=data_cfg.get("num_workers", 4),
        train_ratio=data_cfg.get("train_ratio", 0.7),
        val_ratio=data_cfg.get("val_ratio", 0.15),
        test_ratio=data_cfg.get("test_ratio", 0.15),
        export_features_csv=data_cfg.get("export_features_csv", False),
        features_csv_dir=features_csv_dir,
    )

    return datamodule


def create_model(config: Dict[str, Any], num_sectors: int) -> StockPredictionLitModule:
    """
    モデルを作成

    Args:
        config: 設定辞書
        num_sectors: セクター数

    Returns:
        model: StockPredictionLitModule
    """
    model_cfg = config.get("model", {})
    optimizer_cfg = config.get("optimizer", {})

    model = StockPredictionLitModule(
        model_type=model_cfg.get("model_type", "lstm"),
        lstm_hidden_size=model_cfg.get("lstm_hidden_size", 128),
        lstm_num_layers=model_cfg.get("lstm_num_layers", 2),
        lstm_dropout=model_cfg.get("lstm_dropout", 0.2),
        use_bidirectional=model_cfg.get("use_bidirectional", True),
        num_sectors=num_sectors,
        sector_embedding_dim=model_cfg.get("sector_embedding_dim", 8),
        mlp_hidden_sizes=model_cfg.get("mlp_hidden_sizes", [256, 128, 64]),
        mlp_dropout=model_cfg.get("mlp_dropout", 0.3),
        use_batch_norm=model_cfg.get("use_batch_norm", True),
        attention_dim=model_cfg.get("attention_dim", 64),
        learning_rate=optimizer_cfg.get("learning_rate", 1e-3),
        weight_decay=optimizer_cfg.get("weight_decay", 1e-5),
        use_scheduler=optimizer_cfg.get("use_scheduler", True),
        scheduler_type=optimizer_cfg.get("scheduler_type", "reduce_on_plateau"),
        scheduler_patience=optimizer_cfg.get("scheduler_patience", 10),
        scheduler_factor=optimizer_cfg.get("scheduler_factor", 0.5),
    )

    return model


def create_callbacks(config: Dict[str, Any], dirs: Dict[str, Path]) -> list:
    """
    コールバックを作成

    Args:
        config: 設定辞書
        dirs: ディレクトリパスの辞書

    Returns:
        callbacks: コールバックのリスト
    """
    callbacks = []

    # ModelCheckpoint
    if "checkpoint" in dirs:
        # ベストモデルを best_model.ckpt として保存（固定名）
        checkpoint_callback = ModelCheckpoint(
            dirpath=dirs["checkpoint"],
            filename="best_model",
            monitor="val_loss",
            mode="min",
            save_top_k=1,
            save_last=False,
        )
        callbacks.append(checkpoint_callback)

    # EarlyStopping
    training_cfg = config.get("training", {})
    if training_cfg.get("early_stopping_patience"):
        early_stopping = EarlyStopping(
            monitor="val_loss",
            patience=training_cfg.get("early_stopping_patience", 15),
            mode="min",
            min_delta=training_cfg.get("early_stopping_min_delta", 0.0001),
        )
        callbacks.append(early_stopping)

    # LearningRateMonitor
    lr_monitor = LearningRateMonitor(logging_interval="epoch")
    callbacks.append(lr_monitor)

    return callbacks


def create_loggers(config: Dict[str, Any], dirs: Dict[str, Path]) -> list:
    """
    ロガーを作成

    Args:
        config: 設定辞書
        dirs: ディレクトリパスの辞書

    Returns:
        loggers: ロガーのリスト
    """
    loggers = []
    logging_cfg = config.get("logging", {})

    if "logs" not in dirs:
        return loggers

    # 実験名（タイムスタンプ付き）
    experiment_name = f"stock_prediction_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # TensorBoard Logger
    if logging_cfg.get("use_tensorboard", True):
        tb_logger = TensorBoardLogger(
            save_dir=dirs["logs"],
            name=experiment_name,
        )
        loggers.append(tb_logger)

    # CSV Logger
    if logging_cfg.get("use_csv_logger", True):
        csv_logger = CSVLogger(
            save_dir=dirs["logs"],
            name=experiment_name,
        )
        loggers.append(csv_logger)

    return loggers


def train_model(
    model: StockPredictionLitModule,
    datamodule: LSTMDataModule,
    config: Dict[str, Any],
    callbacks: list,
    loggers: list,
) -> pl.Trainer:
    """
    モデルを学習

    Args:
        model: StockPredictionLitModule
        datamodule: LSTMDataModule
        config: 設定辞書
        callbacks: コールバックのリスト
        loggers: ロガーのリスト

    Returns:
        trainer: PyTorch Lightning Trainer
    """
    training_cfg = config.get("training", {})

    trainer = pl.Trainer(
        max_epochs=training_cfg.get("max_epochs", 100),
        accelerator=training_cfg.get("accelerator", "auto"),
        devices=training_cfg.get("devices", 1),
        precision=training_cfg.get("precision", 32),
        gradient_clip_val=training_cfg.get("gradient_clip_val", 1.0),
        accumulate_grad_batches=training_cfg.get("accumulate_grad_batches", 1),
        callbacks=callbacks,
        logger=loggers,
        deterministic=config.get("deterministic", True),
        enable_progress_bar=True,
        log_every_n_steps=10,
    )

    # 学習実行
    logger.info("=" * 60)
    logger.info("Starting Training")
    logger.info("=" * 60)
    trainer.fit(model, datamodule)

    # テスト実行
    logger.info("=" * 60)
    logger.info("Starting Testing")
    logger.info("=" * 60)
    trainer.test(model, datamodule)

    return trainer


def export_onnx(
    model: StockPredictionLitModule,
    datamodule: LSTMDataModule,
    config: Dict[str, Any],
    dirs: Dict[str, Path],
) -> None:
    """
    ONNXモデルをエクスポート

    Args:
        model: StockPredictionLitModule
        datamodule: LSTMDataModule
        config: 設定辞書
        dirs: ディレクトリパスの辞書
    """
    onnx_cfg = config.get("onnx", {})

    if not onnx_cfg.get("export", True):
        logger.info("ONNX export is disabled")
        return

    if "onnx" not in dirs:
        logger.warning("ONNX directory not configured, skipping export")
        return

    logger.info("=" * 60)
    logger.info("Exporting to ONNX")
    logger.info("=" * 60)

    # ONNX ファイル名（固定名: best_model.onnx）
    onnx_filename = "best_model.onnx"
    onnx_path = dirs["onnx"] / onnx_filename

    # エクスポート
    export_to_onnx(
        model=model,
        output_path=onnx_path,
        opset_version=onnx_cfg.get("opset_version", 14),
        dynamic_axes=onnx_cfg.get("dynamic_axes"),
    )

    # 検証
    verify_onnx_model(onnx_path, model)

    # メタデータ保存
    metadata_path = onnx_path.with_suffix(".json")
    save_model_metadata(
        output_path=metadata_path,
        model=model,
        sector_mapping=datamodule.sector_mapping,
        feature_columns={
            "weekly_features": get_weekly_feature_columns(),
            "static_features": get_static_feature_columns(),
        },
        training_config=config,
    )

    logger.info(f"ONNX model saved: {onnx_path}")
    logger.info(f"Metadata saved: {metadata_path}")

    # S3アップロード（env=s3の場合）
    env = config.get("env", "local")
    if env == "s3":
        s3_cfg = config.get("s3", {})
        output_cfg = s3_cfg.get("output", {})

        logger.info("Uploading ONNX model to S3...")
        bucket = s3_cfg["bucket"]
        onnx_prefix = output_cfg.get("onnx_prefix", "models/onnx")

        # 統一モジュールを使用してONNXモデルとメタデータをアップロード
        upload_onnx_to_s3(
            onnx_path=onnx_path,
            bucket=bucket,
            prefix=onnx_prefix,
            upload_latest=False,  # 固定名best_model.onnxなのでlatestは不要
            upload_metadata=True,
            logger=logger,
        )

    logger.info(f"ONNX export completed: {onnx_path}")


def upload_results_to_s3(config: Dict[str, Any], dirs: Dict[str, Path]) -> None:
    """
    学習結果をS3にアップロード

    Args:
        config: 設定辞書
        dirs: ディレクトリパスの辞書
    """
    from training.utils.s3_utils import upload_directory_to_s3

    env = config.get("env", "local")
    if env != "s3":
        return

    s3_cfg = config.get("s3", {})
    output_cfg = s3_cfg.get("output", {})

    logger.info("=" * 60)
    logger.info("Uploading Results to S3")
    logger.info("=" * 60)

    bucket = s3_cfg["bucket"]

    # チェックポイント
    if "checkpoint" in dirs:
        checkpoint_prefix = output_cfg.get("checkpoint_prefix", "models/checkpoints")
        logger.info(f"Uploading checkpoints to s3://{bucket}/{checkpoint_prefix}")
        upload_directory_to_s3(dirs["checkpoint"], bucket, checkpoint_prefix)

    # ログ
    if "logs" in dirs:
        logs_prefix = output_cfg.get("logs_prefix", "logs")
        logger.info(f"Uploading logs to s3://{bucket}/{logs_prefix}")
        upload_directory_to_s3(dirs["logs"], bucket, logs_prefix)

    logger.info("S3 upload completed")


def parse_args() -> argparse.Namespace:
    """コマンドライン引数をパース"""
    parser = argparse.ArgumentParser(
        description="Train stock prediction LSTM model",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--config",
        type=str,
        default=os.environ.get("CONFIG_PATH", "/workspace/ml/config/train.yaml"),
        help="Path to config yaml file (環境変数: CONFIG_PATH)",
    )

    parser.add_argument(
        "--resume",
        type=str,
        default=None,
        help="Path to checkpoint to resume training from",
    )

    return parser.parse_args()


def main():
    """メイン関数"""
    try:
        # 引数パース
        args = parse_args()
        config_path = Path(args.config)

        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        # 設定読み込み
        logger.info("=" * 60)
        logger.info("Stock Prediction Model Training")
        logger.info("=" * 60)
        logger.info(f"Config file: {config_path}")

        config = load_config(config_path)
        config["_config_path"] = str(config_path)  # 設定ファイルのパスを保存

        env = config.get("env", "local")
        logger.info(f"Environment: {env}")

        # シード設定
        setup_seed(config.get("seed", 42), config.get("deterministic", True))

        # ディレクトリ作成
        dirs = setup_directories(config, config_path)

        # DataModule作成
        logger.info("Creating DataModule...")
        datamodule = create_datamodule(config, config_path)
        datamodule.prepare_data()
        datamodule.setup(stage="fit")

        # モデル作成
        logger.info("Creating Model...")
        num_sectors = len(datamodule.sector_mapping)
        model = create_model(config, num_sectors)
        logger.info(f"\n{model.get_model_summary()}")

        # コールバック・ロガー作成
        callbacks = create_callbacks(config, dirs)
        loggers = create_loggers(config, dirs)

        # 学習実行
        trainer = train_model(model, datamodule, config, callbacks, loggers)

        # ベストモデルの読み込み
        if callbacks and isinstance(callbacks[0], ModelCheckpoint):
            best_model_path = callbacks[0].best_model_path
            if best_model_path:
                logger.info(f"Loading best model from: {best_model_path}")
                model = StockPredictionLitModule.load_from_checkpoint(best_model_path)

        # ONNX エクスポート
        export_onnx(model, datamodule, config, dirs)

        # S3アップロード
        upload_results_to_s3(config, dirs)

        logger.info("=" * 60)
        logger.info("Training Completed Successfully!")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Training failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
