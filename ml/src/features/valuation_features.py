# ml/src/features/valuation_features.py

"""
静的特徴量の計算

仕様書に基づき、以下の6つの静的特徴量を計算:
- 長期統計 (3): LongTermMeanRet, LongTermVol, LongTermMaxDD
- バリュエーション (3): PER, PBR, DividendYield
"""

from __future__ import annotations
from typing import Dict, Optional
import numpy as np
import pandas as pd
import yaml
from pathlib import Path


def calc_long_term_stats(
    weekly_df: pd.DataFrame,
    ticker: str,
    as_of_date: pd.Timestamp,
    lookback_years: int = 3,
) -> Dict[str, float]:
    """
    長期統計特徴量を計算する（過去N年のデータから）

    Args:
        weekly_df: 週次データ
        ticker: ティッカー
        as_of_date: 基準日
        lookback_years: ルックバック期間（年）

    Returns:
        {LongTermMeanRet, LongTermVol, LongTermMaxDD} の辞書
    """
    cutoff_date = as_of_date - pd.DateOffset(years=lookback_years)

    ticker_df = weekly_df[
        (weekly_df["Ticker"] == ticker) &
        (weekly_df["Date"] >= cutoff_date) &
        (weekly_df["Date"] <= as_of_date)
    ].copy()

    if len(ticker_df) < 10:  # 最低10週分のデータが必要
        return {
            "LongTermMeanRet": 0.0,
            "LongTermVol": 0.0,
            "LongTermMaxDD": 0.0,
        }

    ticker_df = ticker_df.sort_values("Date")

    # 週次リターンの平均と標準偏差
    ret = ticker_df["RetWeek"].dropna()
    long_mean = float(ret.mean()) if len(ret) > 0 else 0.0
    long_vol = float(ret.std()) if len(ret) > 1 else 0.0

    # 最大ドローダウン
    close_series = ticker_df["CloseWeek"]
    cummax = close_series.cummax()
    drawdown = (close_series - cummax) / (cummax + 1e-8)
    max_dd = float(drawdown.min()) if len(drawdown) > 0 else 0.0

    return {
        "LongTermMeanRet": long_mean,
        "LongTermVol": long_vol,
        "LongTermMaxDD": max_dd,
    }


def load_valuation_from_universe(
    universe_yaml_path: Path,
    ticker: str,
) -> Dict[str, Optional[float]]:
    """
    ユニバースYAMLからバリュエーション指標を読み込む

    Args:
        universe_yaml_path: ユニバースYAMLのパス
        ticker: ティッカー

    Returns:
        {PER, PBR, DividendYield} の辞書
    """
    with open(universe_yaml_path, "r", encoding="utf-8") as f:
        universe_data = yaml.safe_load(f)

    universe = universe_data.get("universe", [])

    for item in universe:
        if item.get("ticker") == ticker:
            return {
                "PER": item.get("PER"),
                "PBR": item.get("PBR"),
                "DividendYield": item.get("DividendYield"),
            }

    # 見つからない場合はNone
    return {
        "PER": None,
        "PBR": None,
        "DividendYield": None,
    }


def fill_missing_valuation_with_sector_median(
    static_features_df: pd.DataFrame,
    universe_yaml_path: Path,
) -> pd.DataFrame:
    """
    バリュエーション指標の欠損値をセクター中央値で補完する

    Args:
        static_features_df: 静的特徴量DataFrame (columns: Ticker, PER, PBR, DividendYield, ...)
        universe_yaml_path: ユニバースYAMLのパス（セクター情報取得用）

    Returns:
        補完後のDataFrame
    """
    df = static_features_df.copy()

    # ユニバースからセクター情報を取得
    with open(universe_yaml_path, "r", encoding="utf-8") as f:
        universe_data = yaml.safe_load(f)

    universe = universe_data.get("universe", [])
    ticker_to_sector = {item["ticker"]: item.get("sector") for item in universe}

    df["Sector"] = df["Ticker"].map(ticker_to_sector)

    # バリュエーション指標の欠損値を補完
    for col in ["PER", "PBR", "DividendYield"]:
        # Step 1: セクター中央値で埋める
        df[col] = df.groupby("Sector")[col].transform(
            lambda x: x.fillna(x.median())
        )
        # Step 2: それでも欠損なら全体中央値
        df[col] = df[col].fillna(df[col].median())
        # Step 3: まだ欠損なら0
        df[col] = df[col].fillna(0.0)

    df = df.drop(columns=["Sector"])

    return df


def calc_static_features(
    weekly_df: pd.DataFrame,
    universe_yaml_path: Path,
    as_of_date: pd.Timestamp,
    lookback_years: int = 3,
) -> pd.DataFrame:
    """
    全銘柄の静的特徴量を計算する

    Args:
        weekly_df: 週次データ
        universe_yaml_path: ユニバースYAMLのパス
        as_of_date: 基準日
        lookback_years: ルックバック期間（年）

    Returns:
        静的特徴量DataFrame
        columns: [Ticker, LongTermMeanRet, LongTermVol, LongTermMaxDD, PER, PBR, DividendYield]
    """
    tickers = weekly_df["Ticker"].unique()
    records = []

    for ticker in tickers:
        # 長期統計
        long_term = calc_long_term_stats(weekly_df, ticker, as_of_date, lookback_years)

        # バリュエーション
        valuation = load_valuation_from_universe(universe_yaml_path, ticker)

        record = {
            "Ticker": ticker,
            **long_term,
            **valuation,
        }
        records.append(record)

    static_df = pd.DataFrame(records)

    # 欠損値補完
    static_df = fill_missing_valuation_with_sector_median(static_df, universe_yaml_path)

    return static_df


def get_static_feature_columns() -> list[str]:
    """
    静的特徴量のカラム名リストを返す（6特徴）

    Returns:
        特徴量カラム名のリスト
    """
    return [
        # 長期統計 (3)
        "LongTermMeanRet", "LongTermVol", "LongTermMaxDD",
        # バリュエーション (3)
        "PER", "PBR", "DividendYield",
    ]


def extract_static_features(
    static_df: pd.DataFrame,
    ticker: str,
) -> Optional[np.ndarray]:
    """
    特定の銘柄に対して静的特徴量を抽出する

    Args:
        static_df: 静的特徴量DataFrame
        ticker: ティッカー

    Returns:
        (6,) のnumpy配列、またはNone
    """
    feature_cols = get_static_feature_columns()

    ticker_row = static_df[static_df["Ticker"] == ticker]

    if len(ticker_row) == 0:
        return None

    features = ticker_row[feature_cols].values[0]

    # NaN/Infをチェック
    if np.any(~np.isfinite(features)):
        features = np.nan_to_num(features, nan=0.0, posinf=0.0, neginf=0.0)

    return features.astype(np.float32)
