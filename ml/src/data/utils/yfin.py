# ml/src/data/utils/yfin.py

from __future__ import annotations
import time
from datetime import date
from typing import Any, Dict, List, Optional
import pandas as pd
import yfinance as yf


def safe_history(ticker: str, period: str, interval: str, retry: int, sleep_s: float) -> pd.DataFrame:
    """
    yfinance の history() を retry 付きで呼ぶ

    Args:
        ticker (str): 株式のティッカーシンボル
        period (str): データ取得期間
        interval (str): 取得間隔
        retry (int): リトライ回数
        sleep_s (float): リトライ間の待機時間（秒）

    Returns:
        pd.DataFrame: 取得した株価データのデータフレーム

    Raises:
        RuntimeError: すべてのリトライが失敗した場合
    """
    last_err = None
    retry_count = max(1, retry)

    for attempt in range(retry_count):
        try:
            df = yf.Ticker(ticker).history(period=period, interval=interval, auto_adjust=False)
            if not df.empty:
                return df
            last_err = "Empty DataFrame returned"
        except Exception as e:
            last_err = str(e)

        # 最後の試行では sleep しない
        if attempt < retry_count - 1:
            time.sleep(sleep_s)

    raise RuntimeError(
        f"Failed to fetch history for {ticker} after {retry_count} attempt(s). "
        f"Last error: {last_err}"
    )

def normalize_history_index(df: pd.DataFrame) -> pd.DataFrame:
    """
    株価データのインデックスをタイムゾーンなしの日時に変換し、ソートする

    Args:
        df (pd.DataFrame): 株価データのデータフレーム
    Returns:
        pd.DataFrame: インデックスが正規化された株価データのデータフレーム
    """
    dfi = df.copy()
    dfi.index = pd.to_datetime(dfi.index).tz_localize(None)
    dfi.sort_index(inplace=True)
    return dfi

def map_row_fields(row: pd.Series, use_adj: bool, fields: List[str]) -> Dict[str, Any]:
    """
    yfinance の OHLCV 欄を指定の fields に応じて dict 化

    Args:
        row (pd.Series): yfinance の株価データの行
        use_adj (bool): 'close' フィールドに調整後終値を使用するかどうか
        fields (List[str]): 取得するフィールドのリスト
    Returns:
        Dict[str, Any]: 指定されたフィールドを含む辞書
    """
    mapping = {
        "open":     float(row.get("Open")) if pd.notnull(row.get("Open")) else None,
        "high":     float(row.get("High")) if pd.notnull(row.get("High")) else None,
        "low":      float(row.get("Low")) if pd.notnull(row.get("Low")) else None,
        "close":    float(row.get("Close")) if pd.notnull(row.get("Close")) else None,
        "adjclose": float(row.get("Adj Close")) if pd.notnull(row.get("Adj Close")) else None,
        "volume":   int(row.get("Volume")) if pd.notnull(row.get("Volume")) else 0,
    }
    out: Dict[str, Any] = {}
    for k in fields:
        if k == "close" and use_adj and mapping.get("adjclose") is not None:
            out["close"] = mapping["adjclose"]
        else:
            out[k] = mapping.get(k)
    return out


def select_row_for_asof(df: pd.DataFrame, as_of_d: Optional[date]) -> Optional[pd.Series]:
    """
    指定日の直近の株価データの行を選択する
    
    Args:
        df (pd.DataFrame): 株価データのデータフレーム
        as_of_d (Optional[date]): 選択する日付（None の場合は最新行を選択）
    Returns:
        Optional[pd.Series]: 選択された株価データの行、または None
    """
    if df.empty:
        return None

    dfi = normalize_history_index(df)
    if len(dfi) == 0:
        return None

    if as_of_d is None:
        return dfi.iloc[-1]

    cutoff = pd.Timestamp(as_of_d) + pd.Timedelta(days=1) - pd.Timedelta(nanoseconds=1)
    pos = dfi.index.searchsorted(cutoff, side="right") - 1
    if pos < 0:
        return None
    return dfi.iloc[int(pos)]