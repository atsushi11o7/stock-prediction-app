# python/data/fetch_training_data.py

import sys
from pathlib import Path
import yfinance as yf
import pandas as pd
import datetime
import os

repo_dir = Path(__file__).absolute().parents[2]
sys.path.append(repo_dir.as_posix())

def fetch_basic_price_data(ticker: str, period: str = '3y', interval: str = '1mo') -> pd.DataFrame:
    """
    yfinance を使って株価の OHLCV データを取得する。

    Args:
        ticker (str): 株式のティッカーシンボル（ex.'6758.T'）
        period (str): データ取得期間（ex.'3y', '1y'）
        interval (str): 取得間隔（ex.'1d', '1mo'）

    Returns:
        pd.DataFrame: Open, High, Low, Close, Volume を含む株価データフレーム
    """
    stock = yf.Ticker(ticker)
    df = stock.history(period=period, interval=interval)
    df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
    df.reset_index(inplace=True)
    return df

def fetch_fundamentals(ticker: str) -> dict:
    """
    yfinance から株式のファンダメンタル情報を取得する

    Args:
        ticker (str): 株式のティッカーシンボル

    Returns:
        dict: 'MarketCap', 'PER', 'PBR', 'Sector' をキーとする辞書
    """
    info = yf.Ticker(ticker).info
    return {
        'MarketCap': info.get('marketCap', 0),
        'PER': info.get('trailingPE', 0),
        'PBR': info.get('priceToBook', 0),
        'Sector': info.get('sector', 'Unknown')
    }

def merge_price_and_fundamentals(price_df: pd.DataFrame, fundamentals: dict) -> pd.DataFrame:
    """
    株価データとファンダメンタル情報を統合する

    Args:
        price_df (pd.DataFrame): 株価の時系列データ
        fundamentals (dict): ファンダメンタル情報の辞書

    Returns:
        pd.DataFrame: ファンダメンタル情報が追加された株価データフレーム
    """
    for k, v in fundamentals.items():
        price_df[k] = v
    return price_df

def save_to_csv(df: pd.DataFrame, ticker: str, folder: str = 'data/raw'):
    """
    データフレームをCSVファイルとして保存する

    Args:
        df (pd.DataFrame): 保存対象のデータフレーム
        ticker (str): ファイル名に使用するティッカーシンボル
        folder (str): 保存先ディレクトリ

    Returns:
        None
    """
    file_dir = os.path.join(repo_dir, folder)
    os.makedirs(file_dir, exist_ok=True)
    file_path = os.path.join(file_dir, f"{ticker}_merged.csv")
    df.to_csv(file_path, index=False)
    print(f"Data saved to CSV at {file_path}")

if __name__ == '__main__':
    ticker = '6758.T'  # 例: ソニーグループ
    price_df = fetch_basic_price_data(ticker, period='3y', interval='1mo')
    fundamentals = fetch_fundamentals(ticker)
    full_df = merge_price_and_fundamentals(price_df, fundamentals)
    save_to_csv(full_df, ticker)