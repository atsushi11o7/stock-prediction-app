#!/usr/bin/env python3
# ml/src/training/finetune.py

"""
月次ファインチューニングスクリプト（AWS Lambda対応）

既存のPyTorchチェックポイントを直近データでファインチューニング
CPU専用、軽量実装

使用例:
  python src/training/finetune.py --config config/finetune.yaml
"""

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

# モデル定義のインポート
import sys
script_dir = Path(__file__).resolve().parent.parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

from common.logging_config import setup_logger
from common.s3_operations import upload_onnx_to_s3, upload_checkpoint_to_s3
from data.utils.config import (
    resolve_universe_yaml_path,
    load_config,
    get_base_dir,
    get_env_config,
    resolve_path,
)
from data.utils.io import load_daily_data
from model_src.models.lstm_model import StockPredictionLSTM

logger = setup_logger(__name__)


def export_model_to_onnx(
    model: nn.Module,
    output_path: Path,
    opset_version: int = 14,
) -> None:
    """
    純粋なPyTorchモデルをONNXにエクスポート（PyTorch Lightning不要）

    Args:
        model: StockPredictionLSTM モデル
        output_path: 出力パス
        opset_version: ONNX opset バージョン
    """
    model = model.cpu()
    model.eval()

    # ダミー入力データ
    batch_size = 1
    dummy_weekly_seq = torch.randn(batch_size, 156, 23)
    dummy_static_features = torch.randn(batch_size, 6)
    dummy_position_features = torch.randn(batch_size, 2)
    dummy_sector_id = torch.randint(0, 9, (batch_size,))

    # 動的軸設定
    dynamic_axes = {
        "weekly_seq": {0: "batch_size"},
        "static_features": {0: "batch_size"},
        "position_features": {0: "batch_size"},
        "sector_id": {0: "batch_size"},
        "output": {0: "batch_size"},
    }

    # ONNX エクスポート
    torch.onnx.export(
        model,
        (
            dummy_weekly_seq,
            dummy_static_features,
            dummy_position_features,
            dummy_sector_id,
        ),
        output_path,
        export_params=True,
        opset_version=opset_version,
        do_constant_folding=True,
        input_names=["weekly_seq", "static_features", "position_features", "sector_id"],
        output_names=["output"],
        dynamic_axes=dynamic_axes,
    )

    logger.info(f"  ONNX model exported to: {output_path}")


def load_checkpoint_from_local(checkpoint_path: Path) -> Dict[str, Any]:
    """Load PyTorch checkpoint from local file"""
    checkpoint = torch.load(checkpoint_path, map_location=torch.device('cpu'))
    return checkpoint


def load_checkpoint_from_s3(bucket: str, key: str, local_path: Path) -> Dict[str, Any]:
    """Download and load checkpoint from S3"""
    import boto3

    s3_client = boto3.client('s3')

    # Download to local
    logger.info(f"Downloading checkpoint from s3://{bucket}/{key}...")
    s3_client.download_file(bucket, key, str(local_path))

    # Load
    checkpoint = torch.load(local_path, map_location=torch.device('cpu'))
    return checkpoint


def prepare_finetuning_data(
    universe_yaml_path: Path,
    recent_months: int = 1,
    batch_size: int = 32,
    # データソース設定
    source: str = "local",
    path_or_prefix: str = "",
    bucket: str | None = None,
) -> Tuple[DataLoader, int, Dict[str, int]]:
    """
    ファインチューニング用のデータを準備（効率的版）

    直近N ヶ月のデータと、過去データから半分程度を使用
    全データを読み込まず、必要な期間（約3年+α）のみを読み込む
    """
    import pandas as pd
    import yaml

    from features.weekly_features import create_weekly_bars, extract_weekly_sequence
    from features.valuation_features import calc_static_features, extract_static_features
    from data.utils.universe_loader import load_sector_mapping, get_sector_id

    logger.info("\n[INFO] Preparing finetuning data (optimized)...")
    logger.info(f"  Data source: {source}")
    logger.info(f"  Path/Prefix: {path_or_prefix}")
    if bucket:
        logger.info(f"  S3 Bucket: {bucket}")
    logger.info(f"  Universe YAML: {universe_yaml_path}")
    logger.info(f"  Recent months: {recent_months}")

    # 1. 必要な期間のデータを読み込み
    # ファインチューニングでは:
    #   - base_date は最新日付 - 12ヶ月まで使用可能
    #   - base_date から過去156週（3年）の週次特徴量が必要
    # つまり: 最新日付 - 12ヶ月 - 3年 = 最新日付 - 4年分のデータが必要
    # さらに週次特徴量計算のマージンを加えて5年分
    lookback_days = 365 * 5  # 約5年
    logger.info(f"\n[INFO] Loading only recent {lookback_days} days of data...")

    daily_df = load_daily_data(
        source=source,
        path_or_prefix=path_or_prefix,
        bucket=bucket,
        lookback_days=lookback_days,
    )
    logger.info(f"[OK] Loaded {len(daily_df)} daily records (optimized)")

    # 2. 週次特徴量の計算
    logger.info("\n[INFO] Calculating weekly features...")
    weekly_df = create_weekly_bars(
        daily_df,
        as_of_date=None,
        n_weeks=300,  # 156週 × 2（余裕を持たせる）
    )
    logger.info(f"[OK] Generated {len(weekly_df)} weekly bars")

    # 3. 静的特徴量の計算
    logger.info("\n[INFO] Calculating static features...")
    latest_date = daily_df["Date"].max()
    static_df = calc_static_features(
        weekly_df,
        universe_yaml_path,
        as_of_date=latest_date,
        lookback_years=3,
    )
    logger.info(f"[OK] Generated static features for {len(static_df)} tickers")

    # 4. セクターマッピング
    logger.info("\n[INFO] Creating sector mapping...")
    sector_mapping = load_sector_mapping()
    with open(universe_yaml_path, "r", encoding="utf-8") as f:
        universe_data = yaml.safe_load(f)
    universe = universe_data.get("universe", [])
    ticker_to_sector = {item["ticker"]: item.get("sector", "Unknown") for item in universe if item.get("ticker")}
    logger.info(f"[OK] Found {len(sector_mapping)} sectors")

    # 5. サンプル生成（直近データのみから）
    logger.info("\n[INFO] Generating finetuning samples...")
    samples = _generate_finetuning_samples(
        daily_df=daily_df,
        weekly_df=weekly_df,
        recent_months=recent_months,
        n_weeks_input=156,
    )
    logger.info(f"[OK] Generated {len(samples)} finetuning samples")

    # 6. 特徴量を抽出
    logger.info("\n[INFO] Extracting features...")
    weekly_seqs = []
    static_features_list = []
    position_features_list = []
    sector_ids = []
    targets = []

    for sample in samples:
        ticker = sample["ticker"]
        base_date = pd.Timestamp(sample["base_date"])
        target_returns = sample["target_returns"]

        # 週次時系列特徴量 (156, 23)
        weekly_seq = extract_weekly_sequence(weekly_df, ticker, base_date, n_weeks=156)
        if weekly_seq is None:
            weekly_seq = np.zeros((156, 23), dtype=np.float32)

        # 静的特徴量 (6,)
        static_feat = extract_static_features(static_df, ticker)
        if static_feat is None:
            static_feat = np.zeros(6, dtype=np.float32)

        # 位置特徴量 (2,)
        day_of_week = base_date.dayofweek
        week_in_year = base_date.isocalendar()[1]
        week_progress = week_in_year / 52.0
        position_feat = np.array([day_of_week, week_progress], dtype=np.float32)

        # セクターID
        sector = ticker_to_sector.get(ticker, "Unknown")
        sector_id = sector_mapping.get(sector, 0)

        weekly_seqs.append(weekly_seq)
        static_features_list.append(static_feat)
        position_features_list.append(position_feat)
        sector_ids.append(sector_id)
        targets.append(target_returns)

    # NumPy配列に変換
    weekly_seqs = np.array(weekly_seqs, dtype=np.float32)
    static_features_list = np.array(static_features_list, dtype=np.float32)
    position_features_list = np.array(position_features_list, dtype=np.float32)
    sector_ids = np.array(sector_ids, dtype=np.int64)
    targets = np.array(targets, dtype=np.float32)

    logger.info(f"\n[INFO] Feature shapes:")
    logger.info(f"  Weekly seq: {weekly_seqs.shape}")
    logger.info(f"  Static features: {static_features_list.shape}")
    logger.info(f"  Position features: {position_features_list.shape}")
    logger.info(f"  Sector IDs: {sector_ids.shape}")
    logger.info(f"  Targets: {targets.shape}")

    # TensorDataset 作成
    dataset = TensorDataset(
        torch.from_numpy(weekly_seqs),
        torch.from_numpy(static_features_list),
        torch.from_numpy(position_features_list),
        torch.from_numpy(sector_ids),
        torch.from_numpy(targets),
    )

    # DataLoader 作成
    dataloader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=0,
    )

    return dataloader, len(sector_mapping), sector_mapping


def _generate_finetuning_samples(
    daily_df: 'pd.DataFrame',
    weekly_df: 'pd.DataFrame',
    recent_months: int = 1,
    n_weeks_input: int = 156,
) -> List[Dict[str, Any]]:
    """
    ファインチューニング用サンプルを生成

    ファインチューニングでは:
    - base_date: 予測基準日（入力特徴量の最終日）
    - 入力: base_date から過去3年（156週）の週次特徴量
    - ターゲット: base_date から1〜12ヶ月後の各月リターン

    例: 現在が2025/12/21の場合
    - 使用可能なbase_dateの最大値: 2024/12/21（12ヶ月後のデータが存在する必要があるため）
    - 直近1ヶ月分: 2024/11/21 〜 2024/12/21
    - 過去データ: 2024/11/21 より前からランダムサンプリング
    """
    import pandas as pd
    from datetime import timedelta
    import random

    samples = []
    tickers = daily_df["Ticker"].unique()

    # 最新日付
    latest_date = daily_df["Date"].max()

    # base_date の最大値: 12ヶ月後のリターンが計算できる最後の日
    max_base_date = latest_date - timedelta(days=365)

    # 「直近N ヶ月」のカットオフ: max_base_date から N ヶ月前
    recent_cutoff = max_base_date - timedelta(days=recent_months * 30)

    logger.info(f"  Processing {len(tickers)} tickers...")
    logger.info(f"  Latest data date: {latest_date.strftime('%Y-%m-%d')}")
    logger.info(f"  Max base_date (12m before latest): {max_base_date.strftime('%Y-%m-%d')}")
    logger.info(f"  Recent period: {recent_cutoff.strftime('%Y-%m-%d')} ~ {max_base_date.strftime('%Y-%m-%d')}")

    for ticker in tickers:
        ticker_daily = daily_df[daily_df["Ticker"] == ticker].sort_values("Date")

        if len(ticker_daily) < 200:
            continue

        # 直近サンプルと過去サンプルを分けて生成
        recent_samples = []
        historical_samples = []

        for idx in range(len(ticker_daily)):
            base_date = ticker_daily.iloc[idx]["Date"]

            # base_date が max_base_date を超える場合はスキップ
            if base_date > max_base_date:
                continue

            base_price = ticker_daily.iloc[idx]["AdjClose"]

            # base_date時点で156週分のデータがあるかチェック
            weeks_before = weekly_df[
                (weekly_df["Ticker"] == ticker) &
                (weekly_df["Date"] <= base_date)
            ]

            if len(weeks_before) < n_weeks_input:
                continue

            # 1~12ヶ月後の各リターンを計算
            target_returns = []
            valid_sample = True

            for month in range(1, 13):
                target_date = base_date + pd.DateOffset(months=month)
                future_data = ticker_daily[ticker_daily["Date"] >= target_date]

                if len(future_data) == 0:
                    valid_sample = False
                    break

                target_row = future_data.iloc[0]
                target_price = target_row["AdjClose"]
                target_return = np.log(target_price / base_price)
                target_returns.append(float(target_return))

            if not valid_sample:
                continue

            sample = {
                "ticker": ticker,
                "base_date": base_date.isoformat(),
                "target_returns": target_returns,
            }

            # 直近（recent_cutoff 〜 max_base_date）か過去かで分類
            if base_date >= recent_cutoff:
                recent_samples.append(sample)
            else:
                historical_samples.append(sample)

        # 過去サンプルから直近の半分をランダムサンプリング
        num_historical = len(recent_samples) // 2
        if len(historical_samples) > num_historical:
            historical_samples = random.sample(historical_samples, num_historical)

        samples.extend(recent_samples)
        samples.extend(historical_samples)

    logger.info(f"  Total samples generated: {len(samples)}")
    return samples


def finetune_model(
    model: nn.Module,
    dataloader: DataLoader,
    num_epochs: int = 5,
    learning_rate: float = 0.0001,
    device: str = 'cpu',
) -> nn.Module:
    """
    モデルをファインチューニング

    Args:
        model: PyTorchモデル
        dataloader: ファインチューニング用DataLoader
        num_epochs: エポック数（少なめ）
        learning_rate: 学習率（小さめ）
        device: デバイス（'cpu' 固定）

    Returns:
        finetuned_model: ファインチューニング済みモデル
    """
    logger.info(f"\n[INFO] Starting finetuning...")
    logger.info(f"  Epochs: {num_epochs}")
    logger.info(f"  Learning rate: {learning_rate}")
    logger.info(f"  Device: {device}")

    model = model.to(device)
    model.train()

    # Optimizer（学習率は小さめ）
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=learning_rate,
        weight_decay=1e-5,
    )

    # Loss
    criterion = nn.MSELoss()

    # ファインチューニング
    for epoch in range(num_epochs):
        epoch_loss = 0.0
        num_batches = 0

        for batch in dataloader:
            weekly_seq, static_features, position_features, sector_id, target = batch

            # デバイスに転送
            weekly_seq = weekly_seq.to(device)
            static_features = static_features.to(device)
            position_features = position_features.to(device)
            sector_id = sector_id.to(device)
            target = target.to(device)

            # Forward
            optimizer.zero_grad()
            output = model(weekly_seq, static_features, position_features, sector_id)
            loss = criterion(output.squeeze(), target)

            # Backward
            loss.backward()

            # Gradient clipping
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)

            # Update
            optimizer.step()

            epoch_loss += loss.item()
            num_batches += 1

        avg_loss = epoch_loss / num_batches
        print(f"  Epoch [{epoch+1}/{num_epochs}] Loss: {avg_loss:.6f}")

    logger.info("[INFO] Finetuning completed!")
    return model


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="Monthly model finetuning (CPU-only)")
    parser.add_argument(
        "--config",
        type=str,
        default="config/finetune.yaml",
        help="Path to finetune config YAML",
    )
    args = parser.parse_args()

    # 設定ファイルをロード
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = Path(__file__).resolve().parent.parent.parent / config_path

    cfg = load_config(config_path)
    base_dir = get_base_dir(config_path)

    # 環境設定
    env, env_cfg, input_cfg, output_cfg = get_env_config(cfg)

    # ファインチューニング設定
    ft_cfg = cfg.get("finetuning", {})
    recent_months = ft_cfg.get("recent_months", 1)
    num_epochs = ft_cfg.get("num_epochs", 5)
    learning_rate = ft_cfg.get("learning_rate", 0.0001)
    batch_size = ft_cfg.get("batch_size", 32)

    # Universe YAML パスを解決
    universe_yaml_path = resolve_universe_yaml_path(cfg, config_path)

    logger.info("=" * 60)
    logger.info("Monthly Model Finetuning (CPU-only)")
    logger.info("=" * 60)
    logger.info(f"Config: {config_path}")
    logger.info(f"Environment: {env}")
    logger.info(f"Universe YAML: {universe_yaml_path}")
    logger.info(f"Recent months: {recent_months}")
    logger.info(f"Epochs: {num_epochs}")
    logger.info(f"Learning rate: {learning_rate}")
    logger.info("=" * 60)

    # 1. チェックポイントをロード
    logger.info("\n[INFO] Loading checkpoint...")

    if env == "s3":
        # S3からダウンロード
        bucket = cfg["s3"]["bucket"]
        checkpoint_key = input_cfg.get("checkpoint_key", "models/checkpoints/latest.ckpt")
        local_checkpoint_path = Path("/tmp/checkpoint.ckpt")
        checkpoint = load_checkpoint_from_s3(bucket, checkpoint_key, local_checkpoint_path)
        daily_data_dir = None  # S3の場合は別途処理
        s3_daily_prefix = input_cfg.get("daily_data_prefix", "daily")
    else:
        # ローカルから読み込み
        checkpoint_path = resolve_path(
            input_cfg.get("checkpoint_path", "checkpoints/latest.ckpt"), base_dir
        )
        checkpoint = load_checkpoint_from_local(checkpoint_path)
        daily_data_dir = resolve_path(
            input_cfg.get("daily_data_dir", "data/training/daily"), base_dir
        )

    logger.info(f"  Checkpoint loaded successfully")

    # 2. モデルを再構築（純粋なPyTorchで）
    logger.info("\n[INFO] Reconstructing model...")

    # ハイパーパラメータを取得
    hparams = checkpoint.get('hyper_parameters', {})

    # 純粋なPyTorchモデルを作成
    # Note: hparamsのキー名とモデルのパラメータ名が異なる場合があるので、両方対応
    model = StockPredictionLSTM(
        lstm_input_size=hparams.get('lstm_input_size', hparams.get('weekly_input_size', 23)),
        static_feature_size=hparams.get('static_feature_size', hparams.get('static_input_size', 6)),
        position_feature_size=hparams.get('position_feature_size', hparams.get('position_input_size', 2)),
        num_sectors=hparams.get('num_sectors', 9),
        lstm_hidden_size=hparams.get('lstm_hidden_size', 128),
        lstm_num_layers=hparams.get('lstm_num_layers', 2),
        lstm_dropout=hparams.get('lstm_dropout', 0.2),
        use_bidirectional=hparams.get('use_bidirectional', True),
        sector_embedding_dim=hparams.get('sector_embedding_dim', 8),
        mlp_hidden_sizes=hparams.get('mlp_hidden_sizes', [256, 128, 64]),
        mlp_dropout=hparams.get('mlp_dropout', 0.3),
        use_batch_norm=hparams.get('use_batch_norm', True),
    )

    # State dict をロード（Lightning形式 'model.xxx' → 'xxx' に変換）
    state_dict = checkpoint['state_dict']
    model_state_dict = {}
    for key, value in state_dict.items():
        if key.startswith('model.'):
            model_state_dict[key[6:]] = value  # 'model.' prefix を除去
        else:
            model_state_dict[key] = value
    model.load_state_dict(model_state_dict)

    logger.info(f"  Model reconstructed")
    logger.info(f"  Parameters: {sum(p.numel() for p in model.parameters()):,}")

    # 3. ファインチューニング用データを準備
    if env == "s3":
        bucket = cfg["s3"]["bucket"]
        dataloader, num_sectors, sector_mapping = prepare_finetuning_data(
            universe_yaml_path=Path(universe_yaml_path),
            recent_months=recent_months,
            batch_size=batch_size,
            source="s3",
            path_or_prefix=s3_daily_prefix,
            bucket=bucket,
        )
    else:
        dataloader, num_sectors, sector_mapping = prepare_finetuning_data(
            universe_yaml_path=Path(universe_yaml_path),
            recent_months=recent_months,
            batch_size=batch_size,
            source="local",
            path_or_prefix=str(daily_data_dir),
        )

    # 4. ファインチューニング
    finetuned_model = finetune_model(
        model=model,
        dataloader=dataloader,
        num_epochs=num_epochs,
        learning_rate=learning_rate,
        device='cpu',
    )

    # 5. ONNX エクスポート
    logger.info("\n[INFO] Exporting to ONNX...")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # 固定名: best_model.onnx（上書き更新）
    onnx_filename = "best_model.onnx"

    if env == "s3":
        output_dir = Path("/tmp/onnx")
    else:
        output_dir = resolve_path(output_cfg.get("onnx_dir", "models/onnx"), base_dir)

    output_dir.mkdir(parents=True, exist_ok=True)
    onnx_path = output_dir / onnx_filename

    # ONNX エクスポート（純粋なPyTorchで実行）
    export_model_to_onnx(
        model=finetuned_model,
        output_path=onnx_path,
        opset_version=14,
    )

    # メタデータを保存
    metadata_path = onnx_path.with_suffix(".json")

    # sector_mapping は prepare_finetuning_data() から既に取得済み

    metadata = {
        "model_type": hparams.get("model_type", "lstm"),
        "finetuned_timestamp": timestamp,
        "finetuning_params": {
            "recent_months": recent_months,
            "num_epochs": num_epochs,
            "learning_rate": learning_rate,
            "num_samples": len(dataloader.dataset),
        },
        "sector_mapping": sector_mapping,
        "input_spec": {
            "weekly_seq": [156, 23],
            "static_features": [6],
            "position_features": [2],
            "sector_id": [],
        },
        "output_spec": {
            "output": [1],
        },
    }

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    logger.info(f"  Metadata saved: {metadata_path}")

    # 6. S3 アップロード（S3環境の場合）
    if env == "s3":
        try:
            import boto3

            bucket = cfg["s3"]["bucket"]
            s3_prefix = output_cfg.get("onnx_prefix", "models/onnx")

            logger.info(f"\n[INFO] Uploading to S3...")
            s3_client = boto3.client('s3')

            # ONNX モデル（固定名: best_model.onnx）
            s3_key_onnx = f"{s3_prefix}/{onnx_filename}"
            s3_client.upload_file(str(onnx_path), bucket, s3_key_onnx)
            logger.info(f"  Uploaded to s3://{bucket}/{s3_key_onnx}")

            # メタデータ（固定名: best_model.json）
            s3_key_meta = f"{s3_prefix}/{onnx_filename.replace('.onnx', '.json')}"
            s3_client.upload_file(str(metadata_path), bucket, s3_key_meta)
            logger.info(f"  Uploaded to s3://{bucket}/{s3_key_meta}")

        except Exception as e:
            logger.error(f"  ERROR uploading to S3: {e}")

    # 7. チェックポイントも保存（ローカル環境の場合）
    if env == "local":
        checkpoint_dir = resolve_path(output_cfg.get("checkpoint_dir", "checkpoints"), base_dir)
        checkpoint_dir.mkdir(parents=True, exist_ok=True)

        # ファインチューニング済みモデルを best_model.ckpt として上書き保存
        best_ckpt_path = checkpoint_dir / "best_model.ckpt"

        # 純粋なPyTorchで保存（Lightning形式と互換性を保つ）
        torch.save({
            'state_dict': {'model.' + k: v for k, v in finetuned_model.state_dict().items()},
            'hyper_parameters': hparams,
            'finetuned_at': timestamp,
        }, best_ckpt_path)

        logger.info(f"  Checkpoint saved: {best_ckpt_path}")

    # 8. サマリ
    logger.info("\n" + "=" * 60)
    logger.info("Finetuning Complete")
    logger.info("=" * 60)
    logger.info(f"ONNX model: {onnx_path}")
    logger.info(f"Metadata: {metadata_path}")
    logger.info(f"Finetuning samples: {len(dataloader.dataset)}")
    logger.info(f"  Recent {recent_months} month(s): ~{len(dataloader.dataset) * 2 // 3}")
    logger.info(f"  Historical: ~{len(dataloader.dataset) // 3}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
