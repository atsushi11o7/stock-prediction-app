# python/model_src/datamodules/stock_datamodule.py

import sys
from pathlib import Path
import os
import pandas as pd
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
import pytorch_lightning as pl

repo_dir = Path(__file__).absolute().parents[3]
sys.path.append(repo_dir.as_posix())

from python.utils.technical_indicators import add_moving_averages, add_rsi, add_macd

class LSTMDataset(Dataset):
    """
    株価予測のための時系列データセット

    OHLCV、テクニカル指標、ファンダメンタル情報、感情スコア、
    セクター、ティッカー情報の埋め込みを含む時系列データを用いて、次の7営業日の終値を予測する

    Attributes:
        seq_len (int): 入力時系列長
        df (pd.DataFrame): 処理済みデータフレーム
        feature_cols (list): 使用する特徴量名リスト
        values (np.ndarray): 特徴量の値
        targets (np.ndarray): 7日先の終値
        sector_embedding (dict): セクター埋め込み辞書
        ticker_embedding (dict): ティッカー埋め込み辞書
        valid_idx (list): 有効なデータのインデックス
    """
    def __init__(self, df: pd.DataFrame, seq_len: int = 30, sector_embedding: dict = None, ticker_embedding: dict = None):
        self.seq_len = seq_len
        self.df = df.fillna(0.0)

        self.feature_cols = [
            'Open', 'High', 'Low', 'Close', 'Volume',
            'MA_5', 'MA_20', 'RSI', 'MACD',
            'MarketCap', 'PER', 'PBR', 'SentimentScore'
        ]

        self.values = self.df[self.feature_cols].values.astype(np.float32)
        self.targets = self.df['Close'].shift(-1).rolling(7).apply(lambda x: x[-1] if len(x) == 7 else np.nan)
        self.targets = self.targets.shift(-6).values.astype(np.float32)

        self.sector_embedding = sector_embedding if sector_embedding is not None else {}
        self.ticker_embedding = ticker_embedding if ticker_embedding is not None else {}

        self.valid_idx = [i for i in range(len(self.values) - seq_len - 7)
                          if not np.isnan(self.targets[i + seq_len])]

    def __len__(self):
        return len(self.valid_idx)

    def __getitem__(self, i):
        idx = self.valid_idx[i]
        x = self.values[idx: idx + self.seq_len]
        y = self.targets[idx + self.seq_len: idx + self.seq_len + 7]

        sector_embed = self.sector_embedding.get(self.df.iloc[idx]['Sector'], np.zeros(8, dtype=np.float32))
        sector_embed = np.repeat(sector_embed[np.newaxis, :], self.seq_len, axis=0)

        ticker_embed = self.ticker_embedding.get(self.df.iloc[idx]['Ticker'], np.zeros(8, dtype=np.float32))
        ticker_embed = np.repeat(ticker_embed[np.newaxis, :], self.seq_len, axis=0)

        x = np.concatenate([x, sector_embed, ticker_embed], axis=1)

        return torch.tensor(x), torch.tensor(y)

class LSTMDataModule(pl.LightningDataModule):
    """
    株価予測のためのデータモジュール

    OHLCV、テクニカル指標、ファンダメンタル、感情スコア、
    セクター、ティッカー埋め込みを含む特徴量を用いたデータローダーを提供する

    Args:
        data_dir (str): CSVファイルが入っているディレクトリ
        seq_len (int): 入力系列長
        batch_size (int): バッチサイズ
        num_workers (int): DataLoader のワーカー数
    """
    def __init__(self, data_dir: str, seq_len: int = 30, batch_size: int = 64, num_workers: int = 4):
        super().__init__()
        self.data_dir = data_dir
        self.seq_len = seq_len
        self.batch_size = batch_size
        self.num_workers = num_workers

    def load_and_engineer_features(self, folder_path):
        dfs = []
        for filename in os.listdir(folder_path):
            if filename.endswith('.csv'):
                df = pd.read_csv(os.path.join(folder_path, filename), parse_dates=['Date'])
                ticker = filename.replace('_merged.csv', '')
                df['Ticker'] = ticker
                dfs.append(df)
        df = pd.concat(dfs, ignore_index=True)

        df.sort_values(['Ticker', 'Date'], inplace=True)

        # テクニカル指標付与（Tickerごと）
        dfs = []
        for ticker in df['Ticker'].unique():
            sub_df = df[df['Ticker'] == ticker].copy()
            sub_df = add_moving_averages(sub_df)
            sub_df = add_rsi(sub_df)
            sub_df = add_macd(sub_df)
            dfs.append(sub_df)
        df = pd.concat(dfs, ignore_index=True)

        # ファンダメンタル・感情スコア補完
        df['MarketCap'] = df.get('MarketCap', 0)
        df['PER'] = df.get('PER', 0)
        df['PBR'] = df.get('PBR', 0)
        df['SentimentScore'] = df.get('SentimentScore', 0.0)

        # 埋め込み辞書作成
        sectors = df['Sector'].unique()
        tickers = df['Ticker'].unique()
        self.sector_embed = {s: np.eye(len(sectors))[i][:8] for i, s in enumerate(sectors)}
        self.ticker_embed = {t: np.eye(len(tickers))[i][:8] for i, t in enumerate(tickers)}

        return df

    def prepare_data(self):
        df = self.load_and_engineer_features(self.data_dir)
        df.dropna(inplace=True)
        self.df = df

    def setup(self, stage=None):
        total = len(self.df)
        split_idx = int(total * 0.8)
        train_df = self.df.iloc[:split_idx]
        val_df = self.df.iloc[split_idx:]
        self.train_dataset = LSTMDataset(train_df, self.seq_len, self.sector_embed, self.ticker_embed)
        self.val_dataset = LSTMDataset(val_df, self.seq_len, self.sector_embed, self.ticker_embed)

    def train_dataloader(self):
        return DataLoader(self.train_dataset, batch_size=self.batch_size, shuffle=True, num_workers=self.num_workers)

    def val_dataloader(self):
        return DataLoader(self.val_dataset, batch_size=self.batch_size, shuffle=False, num_workers=self.num_workers)
