#!/usr/bin/env python3
# ml/src/inference/predict.py

"""
Daily inference script for AWS Lambda
Uses ONNX model to predict 12-month returns for all universe tickers
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Optional, Any
import argparse

import boto3
import numpy as np
import onnxruntime as ort
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from common.logging_config import setup_logger
from data.utils.universe_loader import load_universe_data, load_sector_mapping
from data.utils.config import (
    load_config as _load_config,
    resolve_universe_yaml_path_with_s3,
    get_base_dir,
)
from data.utils.io import load_daily_data_from_s3, load_daily_data_from_local
from features.weekly_features import create_weekly_bars
from features.position_features import calc_position_features

logger = setup_logger(__name__)


def calc_static_features_for_ticker(
    weekly_df: pd.DataFrame,
    ticker_info: Dict[str, Any],
    lookback_years: int = 3,
) -> np.ndarray:
    """
    Calculate 6 static features for a ticker using weekly data

    Features:
    - LongTermMeanRet: Long-term mean weekly return
    - LongTermVol: Long-term volatility (std of weekly returns)
    - LongTermMaxDD: Maximum drawdown
    - PER: Price-to-Earnings ratio
    - PBR: Price-to-Book ratio
    - DividendYield: Dividend yield
    """
    # Long-term statistics (3 years)
    lookback_weeks = lookback_years * 52
    recent_df = weekly_df.iloc[-lookback_weeks:] if len(weekly_df) > lookback_weeks else weekly_df

    # Mean return
    mean_ret = recent_df["RetWeek"].mean()

    # Volatility
    vol = recent_df["RetWeek"].std()

    # Max drawdown
    cumulative = (1 + recent_df["RetWeek"]).cumprod()
    running_max = cumulative.cummax()
    drawdown = (cumulative - running_max) / running_max
    max_dd = drawdown.min()

    # Valuation metrics from universe YAML
    per = ticker_info.get("PER", 0.0)
    pbr = ticker_info.get("PBR", 0.0)
    div_yield = ticker_info.get("DividendYield", 0.0)

    # Handle None values
    if per is None:
        per = 0.0
    if pbr is None:
        pbr = 0.0
    if div_yield is None:
        div_yield = 0.0

    return np.array([mean_ret, vol, max_dd, per, pbr, div_yield], dtype=np.float32)


def predict_ticker(
    ticker: str,
    ticker_info: Dict[str, Any],
    all_daily_data: pd.DataFrame,
    sector_mapping: Dict[str, int],
    ort_session: ort.InferenceSession,
    as_of_date: Optional[pd.Timestamp] = None,
) -> Dict[str, Any]:
    """Generate prediction for a single ticker"""
    # Filter daily data for this ticker (data already loaded in memory)
    df_daily = all_daily_data[all_daily_data["Ticker"] == ticker].copy()

    if df_daily.empty:
        raise ValueError(f"No data found for ticker: {ticker}")

    if as_of_date is None:
        as_of_date = df_daily["Date"].max()

    # Create weekly features using unified module (156 weeks × 23 features)
    weekly_df = create_weekly_bars(df_daily, as_of_date=as_of_date, n_weeks=156)

    if len(weekly_df) < 156:
        raise ValueError(f"Insufficient data for {ticker}: only {len(weekly_df)} weeks")

    # Extract 23 time-series features
    feature_cols = [
        "OpenWeek", "HighWeek", "LowWeek", "CloseWeek", "VolumeWeek",
        "RetWeek", "Ret4W", "Ret13W", "Ret26W", "Ret52W",
        "MA_4W", "MA_13W", "MA_26W",
        "PriceVsMA_4W", "PriceVsMA_13W", "PriceVsMA_26W",
        "PriceVs52WH", "PriceVs52WL",
        "Vol_13W", "Vol_26W",
        "VolumeRatio",
        "BodyRatio", "ClosePosInRange",
    ]

    # Get only ticker-specific data (remove Ticker, YearWeek, Date columns)
    weekly_seq = weekly_df[feature_cols].values.astype(np.float32)

    # Add batch dimension
    weekly_seq = weekly_seq[np.newaxis, :, :]  # (1, 156, 23)

    # Static features (6 features)
    static_features = calc_static_features_for_ticker(weekly_df, ticker_info)
    static_features = static_features[np.newaxis, :]  # (1, 6)

    # Position features (2 features) using unified module
    position_features = calc_position_features(as_of_date)
    position_features = position_features[np.newaxis, :]  # (1, 2)

    # Sector ID
    sector = ticker_info.get("sector", "Unknown")
    sector_id = sector_mapping.get(sector, 0)
    sector_id_array = np.array([sector_id], dtype=np.int64)  # (1,)

    # Run inference
    inputs = {
        "weekly_seq": weekly_seq,
        "static_features": static_features,
        "position_features": position_features,
        "sector_id": sector_id_array,
    }

    outputs = ort_session.run(None, inputs)
    log_returns = outputs[0][0]  # shape: (12,) - 1~12ヶ月の対数リターン

    # Convert to predicted prices for each month
    current_price = float(weekly_df["CloseWeek"].iloc[-1])

    # 各月の予測株価と通常リターンを計算
    predictions_by_month = []
    for month_idx, log_return in enumerate(log_returns, start=1):
        log_return_float = float(log_return)
        predicted_price = current_price * np.exp(log_return_float)
        normal_return = np.exp(log_return_float) - 1

        predictions_by_month.append({
            "month": month_idx,
            "log_return": round(log_return_float, 6),
            "predicted_price": round(predicted_price, 2),
            "return": round(normal_return, 6),
        })

    return {
        "ticker": ticker,
        "as_of_date": as_of_date.strftime("%Y-%m-%d"),
        "current_price": round(current_price, 2),
        "predictions": predictions_by_month,  # 1~12ヶ月の予測
        # 後方互換性のため12ヶ月後も保持
        "predicted_12m_log_return": round(float(log_returns[-1]), 6),
        "predicted_12m_price": round(current_price * np.exp(float(log_returns[-1])), 2),
        "predicted_12m_return": round(np.exp(float(log_returns[-1])) - 1, 6),
        "sector": sector,
    }


def load_config(config_path: Path) -> Dict[str, Any]:
    """設定ファイルを読み込む"""
    config = _load_config(config_path)

    # universes の解決（環境に応じてローカルまたはS3から取得）
    config["_universe_yaml_path"] = resolve_universe_yaml_path_with_s3(config, config_path)

    return config


@dataclass
class InferenceConfig:
    """推論に必要な設定をまとめたデータクラス"""
    env: str
    universe_yaml_path: str
    daily_data_path: str
    onnx_model_path: Path
    metadata_path: Optional[Path]
    output_dir: Path
    s3_bucket: Optional[str]
    predictions_prefix: Optional[str]

    @property
    def is_s3_env(self) -> bool:
        return self.env == "s3"


def resolve_inference_config(config: Dict[str, Any], config_path: Path) -> InferenceConfig:
    """設定ファイルから推論設定を解決する"""
    project_root = get_base_dir(config_path)
    universe_yaml_path = config.get("_universe_yaml_path")
    if not universe_yaml_path:
        raise ValueError("universes not specified in config defaults")

    env = config.get("env", "local")

    if env == "s3":
        s3_cfg = config.get("s3", {})
        s3_bucket = s3_cfg.get("bucket", "stock-forecast-prod-apne1")
        s3_input_cfg = s3_cfg.get("input", {})
        s3_output_cfg = s3_cfg.get("output", {})

        daily_data_prefix = s3_input_cfg.get("daily_data_prefix", "daily")
        daily_data_path = f"s3://{s3_bucket}/{daily_data_prefix}"
        predictions_prefix = s3_output_cfg.get("predictions_prefix", "predictions")
        output_dir = Path("/tmp/predictions")

        # ONNXモデルをS3からダウンロード
        onnx_key = s3_input_cfg.get("onnx_key", "models/onnx/best_model.onnx")
        onnx_model_path = Path("/tmp") / "best_model.onnx"
        s3_client = boto3.client('s3')
        logger.info(f"Downloading ONNX model from s3://{s3_bucket}/{onnx_key}...")
        s3_client.download_file(s3_bucket, onnx_key, str(onnx_model_path))

        # メタデータもダウンロード（存在する場合）
        metadata_key = onnx_key.replace(".onnx", ".json")
        metadata_path = Path("/tmp") / "best_model.json"
        try:
            s3_client.download_file(s3_bucket, metadata_key, str(metadata_path))
        except Exception:
            metadata_path = None
    else:
        local_cfg = config.get("local", {})
        local_input_cfg = local_cfg.get("input", {})
        local_output_cfg = local_cfg.get("output", {})

        daily_data_dir = local_input_cfg.get("daily_data_dir", "data/training/daily")
        daily_data_path = str(project_root / daily_data_dir)
        output_dir = project_root / local_output_cfg.get("dir", "predictions")
        s3_bucket = None
        predictions_prefix = None

        model_cfg = config.get("model", {})
        onnx_model_path = project_root / model_cfg.get("onnx_path", "models/onnx/best_model.onnx")
        metadata_path = onnx_model_path.with_suffix(".json")

    return InferenceConfig(
        env=env,
        universe_yaml_path=universe_yaml_path,
        daily_data_path=daily_data_path,
        onnx_model_path=onnx_model_path,
        metadata_path=metadata_path,
        output_dir=output_dir,
        s3_bucket=s3_bucket,
        predictions_prefix=predictions_prefix,
    )


def load_all_daily_data(cfg: InferenceConfig) -> pd.DataFrame:
    """日次データを一括で読み込む"""
    logger.info("Loading daily data...")
    if cfg.is_s3_env:
        s3_parts = cfg.daily_data_path[5:].split("/", 1)
        s3_data_bucket = s3_parts[0]
        s3_data_prefix = s3_parts[1] if len(s3_parts) > 1 else ""
        all_daily_data = load_daily_data_from_s3(
            bucket=s3_data_bucket,
            prefix=s3_data_prefix,
        )
    else:
        all_daily_data = load_daily_data_from_local(
            daily_data_dir=Path(cfg.daily_data_path),
        )
    logger.info(f"Loaded {len(all_daily_data)} daily records for {all_daily_data['Ticker'].nunique()} tickers")
    return all_daily_data


def load_sector_mapping_from_metadata(metadata_path: Optional[Path]) -> Dict[str, int]:
    """セクターマッピングを読み込む"""
    if metadata_path and metadata_path.exists():
        logger.info("Loading sector mapping from model metadata...")
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        sector_mapping = metadata.get("sector_mapping", {})
        if not sector_mapping:
            logger.info("Model metadata has no sector_mapping, using sectors.yaml...")
            sector_mapping = load_sector_mapping()
    else:
        logger.info("Loading sector mapping from sectors.yaml...")
        sector_mapping = load_sector_mapping()
    logger.info(f"Loaded sector mapping: {len(sector_mapping)} sectors")
    return sector_mapping


def save_predictions(
    output_data: Dict[str, Any],
    cfg: InferenceConfig,
    as_of_date: str,
) -> None:
    """予測結果を保存する"""
    cfg.output_dir.mkdir(parents=True, exist_ok=True)

    # 1. 日付ファイル（履歴用）
    date_output_path = cfg.output_dir / f"{as_of_date}.json"
    with open(date_output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved predictions to: {date_output_path}")

    # 2. latest.json（最新データ参照用）
    latest_output_path = cfg.output_dir / "latest.json"
    with open(latest_output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    logger.info(f"Updated latest: {latest_output_path}")

    # Upload to S3 if S3 environment
    if cfg.is_s3_env:
        try:
            s3_client = boto3.client('s3')
            logger.info("Uploading to S3...")

            s3_key_date = f"{cfg.predictions_prefix}/{as_of_date}.json"
            s3_client.upload_file(str(date_output_path), cfg.s3_bucket, s3_key_date)
            logger.info(f"  Uploaded to s3://{cfg.s3_bucket}/{s3_key_date}")

            s3_key_latest = f"{cfg.predictions_prefix}/latest.json"
            s3_client.upload_file(str(latest_output_path), cfg.s3_bucket, s3_key_latest)
            logger.info(f"  Uploaded to s3://{cfg.s3_bucket}/{s3_key_latest}")
        except Exception as e:
            logger.error(f"Error uploading to S3: {e}")


def log_summary(predictions: list, errors: list) -> None:
    """推論結果のサマリーをログ出力"""
    logger.info("=" * 60)
    logger.info("Inference Complete")
    logger.info("=" * 60)
    logger.info(f"Successful predictions: {len(predictions)}")
    logger.info(f"Errors: {len(errors)}")
    if predictions:
        returns = [p["predicted_12m_return"] for p in predictions]
        logger.info(f"Average predicted return: {np.mean(returns):+.2%}")
        logger.info(f"Min predicted return: {np.min(returns):+.2%}")
        logger.info(f"Max predicted return: {np.max(returns):+.2%}")
    logger.info("=" * 60)


def main():
    """Main inference function"""
    parser = argparse.ArgumentParser(
        description="Daily stock prediction inference",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 設定ファイルを指定して実行
  python predict.py --config config/predict.yaml

  # 環境変数を使用
  CONFIG_PATH=config/predict.yaml python predict.py
""",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=os.environ.get("CONFIG_PATH"),
        help="Path to config yaml file (環境変数: CONFIG_PATH)",
    )

    args = parser.parse_args()

    # Validate inputs
    if not args.config:
        parser.error("--config is required")

    config_path = Path(args.config)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    # Load and resolve config
    config = load_config(config_path)
    cfg = resolve_inference_config(config, config_path)

    # Log configuration
    logger.info("=" * 60)
    logger.info("Daily Stock Prediction Inference")
    logger.info("=" * 60)
    logger.info(f"Environment: {cfg.env}")
    logger.info(f"Universe YAML: {cfg.universe_yaml_path}")
    logger.info(f"Daily data path: {cfg.daily_data_path}")
    logger.info(f"ONNX model: {cfg.onnx_model_path}")
    logger.info(f"Output dir: {cfg.output_dir}")
    if cfg.is_s3_env:
        logger.info(f"S3 bucket: {cfg.s3_bucket}")
    logger.info("=" * 60)

    # Load resources
    logger.info("Loading universe YAML...")
    universe_data = load_universe_data(cfg.universe_yaml_path)
    tickers = universe_data["tickers"]
    logger.info(f"Found {len(tickers)} tickers")

    logger.info("Loading ONNX model...")
    ort_session = ort.InferenceSession(str(cfg.onnx_model_path))
    logger.info(f"Model loaded: {cfg.onnx_model_path.name}")

    sector_mapping = load_sector_mapping_from_metadata(cfg.metadata_path)
    all_daily_data = load_all_daily_data(cfg)

    # Run predictions
    logger.info("Running predictions...")
    predictions = []
    errors = []

    for i, ticker_data in enumerate(tickers):
        ticker = ticker_data["ticker"]
        try:
            pred = predict_ticker(
                ticker=ticker,
                ticker_info=ticker_data,
                all_daily_data=all_daily_data,
                sector_mapping=sector_mapping,
                ort_session=ort_session,
            )
            predictions.append(pred)
            logger.info(f"[{i+1}/{len(tickers)}] {ticker}: {pred['predicted_12m_return']:+.2%}")
        except Exception as e:
            error_msg = f"{ticker}: {str(e)}"
            errors.append(error_msg)
            logger.error(f"[{i+1}/{len(tickers)}] {error_msg}")

    # Determine as_of_date
    if predictions:
        as_of_date = predictions[0]["as_of_date"]
    else:
        as_of_date = datetime.now().strftime("%Y-%m-%d")

    # Create and save output
    output_data = {
        "as_of": as_of_date,
        "timestamp": datetime.now().isoformat(),
        "model_path": str(cfg.onnx_model_path),
        "universe_path": str(cfg.universe_yaml_path),
        "num_predictions": len(predictions),
        "num_errors": len(errors),
        "predictions": predictions,
        "errors": errors,
    }

    save_predictions(output_data, cfg, as_of_date)
    log_summary(predictions, errors)


if __name__ == "__main__":
    main()
