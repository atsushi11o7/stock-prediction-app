# ml/src/model_src/datamodules/lstm_datamodule.py

"""
LSTM用のPyTorch Lightning DataModule

- 日次データから週次特徴量を生成 (156週 × 23特徴)
- 静的特徴量の取得 (6特徴)
- 位置特徴量の計算 (2特徴)
- セクターエンベディング用のIDマッピング
- 時系列を考慮したtrain/val/test分割
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any
import json

import numpy as np
import pandas as pd
import pytorch_lightning as pl
import torch
from torch.utils.data import Dataset, DataLoader
import yaml

# Feature calculation modules
import sys
script_dir = Path(__file__).resolve().parent.parent.parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

from common.logging_config import setup_logger
from features.weekly_features import create_weekly_bars, get_weekly_feature_columns, extract_weekly_sequence
from features.valuation_features import calc_static_features, get_static_feature_columns, extract_static_features
from data.utils.universe_loader import load_sector_mapping, get_sector_id

logger = setup_logger(__name__)


class StockPredictionDataset(Dataset):
    """
    株価予測用Dataset

    各サンプルは以下を含む:
    - weekly_seq: (156, 23) 週次時系列特徴量
    - static_features: (6,) 静的特徴量
    - position_features: (2,) 位置特徴量 [day_of_week, week_progress]
    - sector_id: int セクターID
    - target: (12,) 1~12ヶ月先の対数リターン
    """

    def __init__(
        self,
        samples: List[Dict[str, Any]],
        weekly_df: pd.DataFrame,
        static_df: pd.DataFrame,
        sector_mapping: Dict[str, int],
        ticker_to_sector: Dict[str, str],
    ):
        """
        Args:
            samples: サンプルのリスト [{ticker, base_date, target_date, target_return}, ...]
            weekly_df: 週次特徴量DataFrame
            static_df: 静的特徴量DataFrame
            sector_mapping: {sector_name: sector_id}
            ticker_to_sector: {ticker: sector_name}
        """
        self.samples = samples
        self.weekly_df = weekly_df
        self.static_df = static_df
        self.sector_mapping = sector_mapping
        self.ticker_to_sector = ticker_to_sector

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        sample = self.samples[idx]
        ticker = sample["ticker"]
        base_date = pd.Timestamp(sample["base_date"])
        target_returns = sample["target_returns"]  # 12個のリターン

        # 週次時系列特徴量 (156, 23)
        weekly_seq = extract_weekly_sequence(
            self.weekly_df,
            ticker,
            base_date,
            n_weeks=156,
        )

        if weekly_seq is None:
            # データ不足の場合はゼロで埋める
            weekly_seq = np.zeros((156, 23), dtype=np.float32)

        # 静的特徴量 (6,)
        static_feat = extract_static_features(self.static_df, ticker)

        if static_feat is None:
            static_feat = np.zeros(6, dtype=np.float32)

        # 位置特徴量 (2,): day_of_week (0-6), week_progress (0-1)
        day_of_week = base_date.dayofweek  # Monday=0, Sunday=6
        week_in_year = base_date.isocalendar()[1]
        week_progress = week_in_year / 52.0
        position_feat = np.array([day_of_week, week_progress], dtype=np.float32)

        # セクターID
        sector = self.ticker_to_sector.get(ticker, "Unknown")
        sector_id = self.sector_mapping.get(sector, 0)

        return {
            "weekly_seq": torch.from_numpy(weekly_seq),
            "static_features": torch.from_numpy(static_feat),
            "position_features": torch.from_numpy(position_feat),
            "sector_id": torch.tensor(sector_id, dtype=torch.long),
            "target": torch.tensor(target_returns, dtype=torch.float32),  # shape: (12,)
        }


class LSTMDataModule(pl.LightningDataModule):
    """
    LSTM用のPyTorch Lightning DataModule

    10年分の日次データから学習用データを生成:
    1. 日次データを読み込み
    2. 週次特徴量を計算 (156週 = 3年分)
    3. 静的特徴量を計算
    4. スライディングウィンドウで最大限のサンプルを生成
    5. 時系列を考慮してtrain/val/test分割
    """

    def __init__(
        self,
        daily_data_dir: str,
        universe_yaml_path: str,
        batch_size: int = 32,
        num_workers: int = 4,
        train_ratio: float = 0.7,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
        n_weeks_input: int = 156,
        target_months: int = 12,
        min_samples_per_ticker: int = 10,
        # CSV出力設定
        export_features_csv: bool = False,
        features_csv_dir: Optional[str] = None,
    ):
        """
        Args:
            daily_data_dir: 日次データディレクトリ (JSONファイル群)
            universe_yaml_path: ユニバースYAMLパス (enriched版)
            batch_size: バッチサイズ
            num_workers: DataLoaderのワーカー数
            train_ratio: 学習データ比率
            val_ratio: 検証データ比率
            test_ratio: テストデータ比率
            n_weeks_input: 入力週数 (デフォルト: 156週 = 3年)
            target_months: ターゲット期間 (月)
            min_samples_per_ticker: 銘柄あたりの最小サンプル数
            export_features_csv: 特徴量をCSVで出力するか
            features_csv_dir: CSV出力先ディレクトリ
        """
        super().__init__()
        self.daily_data_dir = Path(daily_data_dir)
        self.universe_yaml_path = Path(universe_yaml_path)
        self.batch_size = batch_size
        self.num_workers = num_workers
        self.train_ratio = train_ratio
        self.val_ratio = val_ratio
        self.test_ratio = test_ratio
        self.n_weeks_input = n_weeks_input
        self.target_months = target_months
        self.min_samples_per_ticker = min_samples_per_ticker

        # CSV出力設定
        self.export_features_csv = export_features_csv
        self.features_csv_dir = Path(features_csv_dir) if features_csv_dir else Path("/workspace/ml/data/features")

        # データ格納用
        self.daily_df: Optional[pd.DataFrame] = None
        self.weekly_df: Optional[pd.DataFrame] = None
        self.static_df: Optional[pd.DataFrame] = None
        self.sector_mapping: Optional[Dict[str, int]] = None
        self.ticker_to_sector: Optional[Dict[str, str]] = None
        self.train_samples: Optional[List[Dict[str, Any]]] = None
        self.val_samples: Optional[List[Dict[str, Any]]] = None
        self.test_samples: Optional[List[Dict[str, Any]]] = None

    def prepare_data(self) -> None:
        """データのダウンロードなど（シングルプロセスで実行）"""
        # JSONファイルが存在するか確認
        if not self.daily_data_dir.exists():
            raise FileNotFoundError(f"Daily data directory not found: {self.daily_data_dir}")

        if not self.universe_yaml_path.exists():
            raise FileNotFoundError(f"Universe YAML not found: {self.universe_yaml_path}")

    def setup(self, stage: Optional[str] = None) -> None:
        """データの前処理とtrain/val/test分割"""

        # 既にセットアップ済みの場合はスキップ
        if self.train_samples is not None:
            return

        # 1. 日次データの読み込み
        logger.info("Loading daily data from JSON files...")
        self.daily_df = self._load_daily_data()
        logger.info(f"Loaded {len(self.daily_df)} daily records")

        # 2. 週次特徴量の計算
        logger.info("Calculating weekly features...")
        self.weekly_df = create_weekly_bars(
            self.daily_df,
            as_of_date=None,  # 全データを使用
            n_weeks=500,  # 余裕を持たせて500週分計算（約9.6年）
        )
        logger.info(f"Generated {len(self.weekly_df)} weekly bars")

        # 3. 静的特徴量の計算
        logger.info("Calculating static features...")
        latest_date = self.daily_df["Date"].max()
        self.static_df = calc_static_features(
            self.weekly_df,
            self.universe_yaml_path,
            as_of_date=latest_date,
            lookback_years=3,
        )
        logger.info(f"Generated static features for {len(self.static_df)} tickers")

        # 4. セクターマッピングの作成
        logger.info("Creating sector mapping...")
        self.sector_mapping, self.ticker_to_sector = self._create_sector_mapping()
        logger.info(f"Found {len(self.sector_mapping)} sectors")

        # 5. サンプル生成
        logger.info("Generating training samples...")
        all_samples = self._generate_samples()
        logger.info(f"Generated {len(all_samples)} samples")

        # 6. 時系列分割
        logger.info("Splitting into train/val/test...")
        self.train_samples, self.val_samples, self.test_samples = self._time_series_split(all_samples)
        logger.info(f"Train: {len(self.train_samples)}, Val: {len(self.val_samples)}, Test: {len(self.test_samples)}")

        # 7. CSV出力（オプション）
        if self.export_features_csv:
            logger.info("Exporting features to CSV...")
            self._export_features_to_csv()
            logger.info("Features exported")

    def _load_daily_data(self) -> pd.DataFrame:
        """全JSON ファイルから日次データを読み込む"""
        json_files = sorted(self.daily_data_dir.glob("*.json"))
        json_files = [f for f in json_files if f.name != "latest.json"]

        if not json_files:
            raise ValueError(f"No JSON files found in {self.daily_data_dir}")

        records = []
        for json_file in json_files:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            date_str = data.get("as_of")
            symbols = data.get("symbols", [])

            for sym in symbols:
                sym["Date"] = date_str
                records.append(sym)

        df = pd.DataFrame(records)
        df["Date"] = pd.to_datetime(df["Date"])

        # カラム名を標準化（小文字 → 大文字）
        column_mapping = {
            "ticker": "Ticker",
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "adjclose": "AdjClose",
            "volume": "Volume",
        }

        df = df.rename(columns=column_mapping)

        # 必要なカラムを確認
        required_cols = ["Date", "Ticker", "Open", "High", "Low", "Close", "AdjClose", "Volume"]
        missing_cols = set(required_cols) - set(df.columns)
        if missing_cols:
            raise ValueError(f"Missing required columns in daily data: {missing_cols}")

        return df.sort_values(["Ticker", "Date"])

    def _create_sector_mapping(self) -> Tuple[Dict[str, int], Dict[str, str]]:
        """
        セクターマッピングを作成

        - sectors.yaml からセクター名→IDのマスターマッピングを読み込み
        - universe YAML から各ティッカーのセクター名を取得
        """
        # 1. sectors.yaml からマスターマッピングを読み込み
        sector_mapping = load_sector_mapping()

        # 2. universe YAML から各ティッカーのセクター名を取得
        with open(self.universe_yaml_path, "r", encoding="utf-8") as f:
            universe_data = yaml.safe_load(f)

        universe = universe_data.get("universe", [])
        ticker_to_sector = {}

        for item in universe:
            ticker = item.get("ticker")
            sector = item.get("sector", "Unknown")

            if ticker:
                ticker_to_sector[ticker] = sector

        return sector_mapping, ticker_to_sector

    def _generate_samples(self) -> List[Dict[str, Any]]:
        """スライディングウィンドウでサンプルを生成"""
        samples = []
        tickers = self.daily_df["Ticker"].unique()

        logger.info(f"Processing {len(tickers)} tickers...")

        for ticker_idx, ticker in enumerate(tickers):
            ticker_daily = self.daily_df[self.daily_df["Ticker"] == ticker].sort_values("Date")

            if len(ticker_daily) < 200:  # 最低限のデータが必要
                logger.debug(f"[{ticker}] Skipped: only {len(ticker_daily)} days")
                continue

            ticker_samples = 0

            # 各営業日を base_date としてサンプル生成
            # base_date: 予測基準日
            # target_dates: base_date の1~12ヶ月後
            for idx in range(len(ticker_daily)):
                base_date = ticker_daily.iloc[idx]["Date"]
                base_price = ticker_daily.iloc[idx]["AdjClose"]

                # base_date時点で156週分のデータがあるかチェック
                weeks_before = self.weekly_df[
                    (self.weekly_df["Ticker"] == ticker) &
                    (self.weekly_df["Date"] <= base_date)
                ]

                if len(weeks_before) < self.n_weeks_input:
                    continue

                # 1~12ヶ月後の各リターンを計算
                target_returns = []
                target_dates = []
                valid_sample = True

                for month in range(1, 13):
                    target_date = base_date + pd.DateOffset(months=month)
                    future_data = ticker_daily[ticker_daily["Date"] >= target_date]

                    if len(future_data) == 0:
                        valid_sample = False
                        break

                    # 最も近いN ヶ月後の価格を取得
                    target_row = future_data.iloc[0]
                    target_price = target_row["AdjClose"]
                    target_date_actual = target_row["Date"]

                    # 対数リターンを計算
                    target_return = np.log(target_price / base_price)
                    target_returns.append(target_return)
                    target_dates.append(target_date_actual.isoformat())

                if not valid_sample:
                    continue

                samples.append({
                    "ticker": ticker,
                    "base_date": base_date.isoformat(),
                    "target_dates": target_dates,  # 12個の日付
                    "target_date": target_dates[-1],  # 後方互換性のため12ヶ月後も保持
                    "target_returns": [float(r) for r in target_returns],  # 12個のリターン
                    "target_return": float(target_returns[-1]),  # 後方互換性のため12ヶ月後も保持
                })

                ticker_samples += 1

            if ticker_samples > 0:
                logger.debug(f"[{ticker_idx+1}/{len(tickers)}] {ticker}: {ticker_samples} samples")
            else:
                # デバッグ情報
                weeks = len(self.weekly_df[self.weekly_df["Ticker"] == ticker])
                logger.debug(f"[{ticker_idx+1}/{len(tickers)}] {ticker}: 0 samples (weekly bars: {weeks})")

        return samples

    def _time_series_split(
        self,
        samples: List[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """時系列を考慮してtrain/val/test分割"""
        # base_dateでソート
        samples_sorted = sorted(samples, key=lambda x: x["base_date"])

        n_total = len(samples_sorted)
        n_train = int(n_total * self.train_ratio)
        n_val = int(n_total * self.val_ratio)

        train = samples_sorted[:n_train]
        val = samples_sorted[n_train:n_train + n_val]
        test = samples_sorted[n_train + n_val:]

        return train, val, test

    def train_dataloader(self) -> DataLoader:
        """学習用DataLoader"""
        dataset = StockPredictionDataset(
            self.train_samples,
            self.weekly_df,
            self.static_df,
            self.sector_mapping,
            self.ticker_to_sector,
        )

        return DataLoader(
            dataset,
            batch_size=self.batch_size,
            shuffle=True,
            num_workers=self.num_workers,
            pin_memory=True,
        )

    def val_dataloader(self) -> DataLoader:
        """検証用DataLoader"""
        dataset = StockPredictionDataset(
            self.val_samples,
            self.weekly_df,
            self.static_df,
            self.sector_mapping,
            self.ticker_to_sector,
        )

        return DataLoader(
            dataset,
            batch_size=self.batch_size,
            shuffle=False,
            num_workers=self.num_workers,
            pin_memory=True,
        )

    def test_dataloader(self) -> DataLoader:
        """テスト用DataLoader"""
        dataset = StockPredictionDataset(
            self.test_samples,
            self.weekly_df,
            self.static_df,
            self.sector_mapping,
            self.ticker_to_sector,
        )

        return DataLoader(
            dataset,
            batch_size=self.batch_size,
            shuffle=False,
            num_workers=self.num_workers,
            pin_memory=True,
        )

    def _export_features_to_csv(self) -> None:
        """
        特徴量をCSVファイルに出力

        出力ファイル:
        - weekly_features.csv: 週次時系列特徴量（全週・全銘柄）
        - static_features.csv: 静的特徴量（全銘柄）
        - samples_train.csv: 学習サンプル情報
        - samples_val.csv: 検証サンプル情報
        - samples_test.csv: テストサンプル情報
        """
        # 出力ディレクトリの作成
        self.features_csv_dir.mkdir(parents=True, exist_ok=True)

        # 1. 週次時系列特徴量の出力
        logger.info("[1/5] Exporting weekly features to CSV...")
        weekly_csv_path = self.features_csv_dir / "weekly_features.csv"
        self.weekly_df.to_csv(weekly_csv_path, index=False, encoding="utf-8")
        logger.info(f"  -> {weekly_csv_path} ({len(self.weekly_df)} rows)")

        # 2. 静的特徴量の出力
        logger.info("[2/5] Exporting static features to CSV...")
        static_csv_path = self.features_csv_dir / "static_features.csv"
        self.static_df.to_csv(static_csv_path, index=False, encoding="utf-8")
        logger.info(f"  -> {static_csv_path} ({len(self.static_df)} rows)")

        # 3. サンプル情報の出力（Train）
        logger.info("[3/5] Exporting training samples to CSV...")
        train_samples_df = pd.DataFrame(self.train_samples)
        train_csv_path = self.features_csv_dir / "samples_train.csv"
        train_samples_df.to_csv(train_csv_path, index=False, encoding="utf-8")
        logger.info(f"  -> {train_csv_path} ({len(train_samples_df)} rows)")

        # 4. サンプル情報の出力（Validation）
        logger.info("[4/5] Exporting validation samples to CSV...")
        val_samples_df = pd.DataFrame(self.val_samples)
        val_csv_path = self.features_csv_dir / "samples_val.csv"
        val_samples_df.to_csv(val_csv_path, index=False, encoding="utf-8")
        logger.info(f"  -> {val_csv_path} ({len(val_samples_df)} rows)")

        # 5. サンプル情報の出力（Test）
        logger.info("[5/5] Exporting test samples to CSV...")
        test_samples_df = pd.DataFrame(self.test_samples)
        test_csv_path = self.features_csv_dir / "samples_test.csv"
        test_samples_df.to_csv(test_csv_path, index=False, encoding="utf-8")
        logger.info(f"  -> {test_csv_path} ({len(test_samples_df)} rows)")

        # サマリ情報の出力
        summary_path = self.features_csv_dir / "summary.txt"
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            f.write("Feature Export Summary\n")
            f.write("=" * 60 + "\n\n")

            f.write("[Weekly Features]\n")
            f.write(f"  File: weekly_features.csv\n")
            f.write(f"  Rows: {len(self.weekly_df)}\n")
            f.write(f"  Columns: {len(self.weekly_df.columns)}\n")
            f.write(f"  Column names: {', '.join(self.weekly_df.columns.tolist())}\n\n")

            f.write("[Static Features]\n")
            f.write(f"  File: static_features.csv\n")
            f.write(f"  Rows: {len(self.static_df)}\n")
            f.write(f"  Columns: {len(self.static_df.columns)}\n")
            f.write(f"  Column names: {', '.join(self.static_df.columns.tolist())}\n\n")

            f.write("[Samples]\n")
            f.write(f"  Training: {len(self.train_samples)} samples\n")
            f.write(f"  Validation: {len(self.val_samples)} samples\n")
            f.write(f"  Test: {len(self.test_samples)} samples\n")
            f.write(f"  Total: {len(self.train_samples) + len(self.val_samples) + len(self.test_samples)} samples\n\n")

            f.write("[Sector Mapping]\n")
            for sector, sector_id in sorted(self.sector_mapping.items(), key=lambda x: x[1]):
                f.write(f"  {sector_id}: {sector}\n")

        logger.info(f"  -> {summary_path}")
        logger.info(f"All features exported to: {self.features_csv_dir}")
