# ml/src/features/position_features.py

"""
ポジション特徴量の計算

年間サイクル性を捉えるため、週番号をsin/cos変換した2特徴を計算する。
"""

from __future__ import annotations
import numpy as np
import pandas as pd


def calc_position_features(as_of_date: pd.Timestamp) -> np.ndarray:
    """
    ポジション特徴量を計算する（年間サイクル性）

    Args:
        as_of_date: 基準日

    Returns:
        (2,) のnumpy配列 [sin_week, cos_week]

    Example:
        >>> import pandas as pd
        >>> date = pd.Timestamp("2025-01-15")
        >>> features = calc_position_features(date)
        >>> print(features.shape)
        (2,)
    """
    # ISO週番号を取得
    week_of_year = as_of_date.isocalendar()[1]
    week_frac = week_of_year / 52.0

    # sin/cos変換で周期性を表現
    sin_week = np.sin(2 * np.pi * week_frac)
    cos_week = np.cos(2 * np.pi * week_frac)

    return np.array([sin_week, cos_week], dtype=np.float32)
