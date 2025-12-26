# ml/src/data/utils/aggregate.py

from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

from .yfin import map_row_fields, normalize_history_index


def build_by_date(
    ticker: str,
    df: pd.DataFrame,
    use_adj: bool,
    fields: List[str],
) -> Tuple[Dict[str, List[Dict[str, Any]]], Optional[pd.Timestamp]]:
    """
    yfinance の history DataFrame から日付ごとのデータ構造を構築する
    
    Args:
        ticker (str): 株式のティッカーシンボル
        df (pd.DataFrame): yfinance の history DataFrame
        use_adj (bool): 'close' フィールドに調整後終値を使用するかどうか
        fields (List[str]): 取得するフィールドのリスト
    Returns:
        Tuple[Dict[str, List[Dict[str, Any]]], Optional[pd.Timestamp]]:
            - 日付ごとのデータ構造
            - 最新の日時（Timestamp）
    """
    by_date: Dict[str, List[Dict[str, Any]]] = {}
    latest_dt: Optional[pd.Timestamp] = None

    dfi = normalize_history_index(df)
    for idx, row in dfi.iterrows():
        day_str = idx.date().isoformat()
        rec: Dict[str, Any] = {"ticker": ticker}
        rec.update(map_row_fields(row, use_adj, fields))
        by_date.setdefault(day_str, []).append(rec)
        if latest_dt is None or idx > latest_dt:
            latest_dt = idx

    return by_date, latest_dt
