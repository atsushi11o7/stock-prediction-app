# python/data/retrieval.py

import os
import yfinance as yf
import pandas as pd

def fetch_stock_data(ticker: str, period: str = '1y', interval: str = '1d') -> pd.DataFrame:
    """
    Yahoo Finance から指定された銘柄の株価データを取得する関数
    :param ticker: 株式銘柄コード（例: 'AAPL'）
    :param period: データ取得期間（例: '1y' は過去1年分）
    :param interval: データの間隔（例: '1d' は1日ごと）
    :return: pandas DataFrame 形式の株価データ
    """
    print(f"Fetching data for {ticker} for period {period} with interval {interval}...")
    stock = yf.Ticker(ticker)
    data = stock.history(period=period, interval=interval)
    return data

def save_data_to_csv(data: pd.DataFrame, ticker: str, folder: str = 'data/raw') -> None:
    """
    取得したデータを CSV ファイルとして保存する関数
    :param data: 株価データ DataFrame
    :param ticker: 銘柄コード
    :param folder: 保存先フォルダ
    """
    os.makedirs(folder, exist_ok=True)
    file_path = os.path.join(folder, f"{ticker}_data.csv")
    data.to_csv(file_path)
    print(f"Data saved to {file_path}")

if __name__ == '__main__':
    # ex. Apple の株価データを取得
    ticker = 'AAPL'
    data = fetch_stock_data(ticker)
    print(data.head())
    save_data_to_csv(data, ticker)
