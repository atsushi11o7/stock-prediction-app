# python/data/retrieval.py

import logging
import sys
from pathlib import Path
import os
import json
import logging
import pandas as pd
import yfinance as yf
from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

repo_dir = Path(__file__).absolute().parents[2]
sys.path.append(repo_dir.as_posix())

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

'''
# 環境変数で管理されたデータベース接続URI
DATABASE_URI = os.getenv('DATABASE_URI', 'postgresql+psycopg2://user:password@localhost:5432/stockdb')

# SQLAlchemy のベースクラス
Base = declarative_base()

class StockPrice(Base):
    """
    株価データを格納するテーブル定義
    """
    __tablename__ = 'stock_prices'
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime, index=True, nullable=False)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)

# データベースエンジンとセッションの生成
engine = create_engine(DATABASE_URI)
SessionLocal = sessionmaker(bind=engine)

# テーブル作成
Base.metadata.create_all(engine)
'''


def fetch_stock_data(ticker: str, period: str = '1y', interval: str = '1d') -> pd.DataFrame:
    """
    指定した銘柄の株価データを Yahoo Finance から取得する

    Args:
        ticker (str): 株式銘柄コード（ex. 'AAPL'）
        period (str, optional): データ取得期間（ex. '1y'), デフォルトは '1y'
        interval (str, optional): データの間隔（ex. '1d'), デフォルトは '1d'

    Returns:
        pd.DataFrame: 日付をインデックスとする株価データ
    """
    logger.info(f"Fetching data for {ticker} (period={period}, interval={interval})")
    stock = yf.Ticker(ticker)
    data = stock.history(period=period, interval=interval)
    return data


def save_data_to_db(data: pd.DataFrame, ticker: str) -> None:
    """
    DataFrame の株価データをデータベースに保存する

    Args:
        data (pd.DataFrame): インデックスが日付の株価データ
        ticker (str): 銘柄コード
    """
    session = SessionLocal()
    records = []
    df = data.reset_index().rename(columns={'Date': 'timestamp'})

    for _, row in df.iterrows():
        record = StockPrice(
            ticker=ticker,
            timestamp=row['timestamp'],
            open=row['Open'],
            high=row['High'],
            low=row['Low'],
            close=row['Close'],
            volume=row['Volume'],
        )
        records.append(record)

    session.bulk_save_objects(records)
    session.commit()
    session.close()
    logger.info(f"Saved {len(records)} records to database for {ticker}")


def save_data_to_csv(data: pd.DataFrame, ticker: str, folder: str = 'data/raw') -> None:
    """
    取得した株価データを CSV ファイルとして保存する

    Args:
        data (pd.DataFrame): 株価データ
        ticker (str): 株式銘柄コード
        folder (str, optional): 保存先フォルダのパス, デフォルトは 'data/raw'
    """
    file_dir = os.path.join(repo_dir, folder)
    os.makedirs(file_dir, exist_ok=True)
    file_path = os.path.join(file_dir, f"{ticker}_data.csv")
    data.to_csv(file_path)
    logger.info(f"Data saved to CSV at {file_path}")


if __name__ == '__main__':
    # ex. Apple の株価データを取得してDBとCSVに保存
    ticker = 'AAPL'
    data = fetch_stock_data(ticker)
    #save_data_to_db(data, ticker)
    save_data_to_csv(data, ticker)
