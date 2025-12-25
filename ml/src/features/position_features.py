# ml/src/features/position_features.py

"""
ポジション特徴量の計算

時間的な位置情報を表す特徴量を計算する。
"""

from __future__ import annotations
import numpy as np
import pandas as pd

from common.constants import WEEKS_PER_YEAR


def calc_position_features(as_of_date: pd.Timestamp) -> np.ndarray:
    """
    ポジション特徴量を計算する

    Args:
        as_of_date: 基準日

    Returns:
        (2,) のnumpy配列 [day_of_week, week_progress]
        - day_of_week: 曜日 (0=月曜, 6=日曜)
        - week_progress: 年間進捗 (1週目=1/52, 52週目=1.0)

    Example:
        >>> import pandas as pd
        >>> date = pd.Timestamp("2025-01-15")
        >>> features = calc_position_features(date)
        >>> print(features.shape)
        (2,)
    """
    # 曜日 (0=Monday, 6=Sunday)
    day_of_week = as_of_date.dayofweek

    # ISO週番号から年間進捗を計算
    week_of_year = as_of_date.isocalendar()[1]
    week_progress = week_of_year / float(WEEKS_PER_YEAR)

    return np.array([day_of_week, week_progress], dtype=np.float32)
