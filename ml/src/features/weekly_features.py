# ml/src/features/weekly_features.py

"""
週次時系列特徴量の計算

仕様書に基づき、日次OHLCVデータから週次バーを生成し、
23個の時系列特徴量を計算する。
"""

from __future__ import annotations
from typing import Optional
import numpy as np
import pandas as pd


def create_weekly_bars(
    df_daily: pd.DataFrame,
    as_of_date: Optional[pd.Timestamp] = None,
    n_weeks: int = 156,
) -> pd.DataFrame:
    """
    日次データから週次バーを生成し、23個の時系列特徴量を計算する

    Args:
        df_daily: 日次データ (columns: Date, Ticker, Open, High, Low, Close, AdjClose, Volume)
        as_of_date: 基準日（Noneの場合は全データを使用）
        n_weeks: 取得する週数（デフォルト: 156週 = 3年）

    Returns:
        週次特徴量DataFrame (columns: Ticker, YearWeek, Date, 23特徴量...)

    週次特徴量（23特徴）:
    - OHLCV (5): OpenWeek, HighWeek, LowWeek, CloseWeek, VolumeWeek
    - リターン (5): RetWeek, Ret4W, Ret13W, Ret26W, Ret52W
    - 移動平均 (3): MA_4W, MA_13W, MA_26W
    - トレンド位置 (3): PriceVsMA_4W, PriceVsMA_13W, PriceVsMA_26W
    - 高値安値位置 (2): PriceVs52WH, PriceVs52WL
    - ボラティリティ (2): Vol_13W, Vol_26W
    - 出来高 (1): VolumeRatio
    - ローソク足形状 (2): BodyRatio, ClosePosInRange
    """
    df = df_daily.copy()
    df["Date"] = pd.to_datetime(df["Date"])

    # as_of_date時点までのデータのみ使用
    if as_of_date is not None:
        df = df[df["Date"] <= as_of_date]

    df = df.sort_values(["Ticker", "Date"])

    # ISO週番号を付与
    df["YearWeek"] = df["Date"].dt.strftime("%G-W%V")

    weekly_records = []

    for ticker, g_ticker in df.groupby("Ticker"):
        # 週ごとに集約
        weekly_bars = []

        for year_week, g_week in g_ticker.groupby("YearWeek"):
            g_week = g_week.sort_values("Date")

            bar = {
                "Ticker": ticker,
                "YearWeek": year_week,
                "Date": g_week.iloc[-1]["Date"],  # 週末日
                # OHLCV
                "OpenWeek": float(g_week.iloc[0]["Open"]),
                "HighWeek": float(g_week["High"].max()),
                "LowWeek": float(g_week["Low"].min()),
                "CloseWeek": float(g_week.iloc[-1]["AdjClose"]),
                "VolumeWeek": int(g_week["Volume"].sum()),
            }
            weekly_bars.append(bar)

        weekly_df = pd.DataFrame(weekly_bars)
        weekly_df = weekly_df.sort_values("Date")

        # 週次リターン
        weekly_df["RetWeek"] = weekly_df["CloseWeek"].pct_change()

        # 累積リターン
        weekly_df["Ret4W"] = weekly_df["CloseWeek"].pct_change(4)
        weekly_df["Ret13W"] = weekly_df["CloseWeek"].pct_change(13)
        weekly_df["Ret26W"] = weekly_df["CloseWeek"].pct_change(26)
        weekly_df["Ret52W"] = weekly_df["CloseWeek"].pct_change(52)

        # 移動平均
        weekly_df["MA_4W"] = weekly_df["CloseWeek"].rolling(4, min_periods=1).mean()
        weekly_df["MA_13W"] = weekly_df["CloseWeek"].rolling(13, min_periods=1).mean()
        weekly_df["MA_26W"] = weekly_df["CloseWeek"].rolling(26, min_periods=1).mean()

        # MAからの乖離率
        weekly_df["PriceVsMA_4W"] = weekly_df["CloseWeek"] / weekly_df["MA_4W"] - 1
        weekly_df["PriceVsMA_13W"] = weekly_df["CloseWeek"] / weekly_df["MA_13W"] - 1
        weekly_df["PriceVsMA_26W"] = weekly_df["CloseWeek"] / weekly_df["MA_26W"] - 1

        # 52週高値・安値
        weekly_df["High52W"] = weekly_df["HighWeek"].rolling(52, min_periods=1).max()
        weekly_df["Low52W"] = weekly_df["LowWeek"].rolling(52, min_periods=1).min()
        weekly_df["PriceVs52WH"] = weekly_df["CloseWeek"] / weekly_df["High52W"] - 1
        weekly_df["PriceVs52WL"] = weekly_df["CloseWeek"] / weekly_df["Low52W"] - 1

        # ボラティリティ
        weekly_df["Vol_13W"] = weekly_df["RetWeek"].rolling(13, min_periods=1).std()
        weekly_df["Vol_26W"] = weekly_df["RetWeek"].rolling(26, min_periods=1).std()

        # 出来高比率
        weekly_df["VolumeMA_13W"] = weekly_df["VolumeWeek"].rolling(13, min_periods=1).mean()
        weekly_df["VolumeRatio"] = weekly_df["VolumeWeek"] / (weekly_df["VolumeMA_13W"] + 1e-8)

        # ローソク足形状
        weekly_df["BodyRatio"] = (
            abs(weekly_df["CloseWeek"] - weekly_df["OpenWeek"]) /
            (weekly_df["HighWeek"] - weekly_df["LowWeek"] + 1e-8)
        )
        weekly_df["ClosePosInRange"] = (
            (weekly_df["CloseWeek"] - weekly_df["LowWeek"]) /
            (weekly_df["HighWeek"] - weekly_df["LowWeek"] + 1e-8)
        )

        # 最新n_weeks分のみ取得
        weekly_df = weekly_df.tail(n_weeks).copy()

        weekly_records.append(weekly_df)

    if not weekly_records:
        return pd.DataFrame()

    result = pd.concat(weekly_records, ignore_index=True)
    return result


def get_weekly_feature_columns() -> list[str]:
    """
    週次時系列特徴量のカラム名リストを返す（23特徴）

    Returns:
        特徴量カラム名のリスト
    """
    return [
        # OHLCV (5)
        "OpenWeek", "HighWeek", "LowWeek", "CloseWeek", "VolumeWeek",
        # リターン (5)
        "RetWeek", "Ret4W", "Ret13W", "Ret26W", "Ret52W",
        # 移動平均 (3)
        "MA_4W", "MA_13W", "MA_26W",
        # トレンド位置 (3)
        "PriceVsMA_4W", "PriceVsMA_13W", "PriceVsMA_26W",
        # 高値安値位置 (2)
        "PriceVs52WH", "PriceVs52WL",
        # ボラティリティ (2)
        "Vol_13W", "Vol_26W",
        # 出来高 (1)
        "VolumeRatio",
        # ローソク足形状 (2)
        "BodyRatio", "ClosePosInRange",
    ]


def extract_weekly_sequence(
    weekly_df: pd.DataFrame,
    ticker: str,
    end_date: pd.Timestamp,
    n_weeks: int = 156,
) -> Optional[np.ndarray]:
    """
    特定の銘柄・日付に対して、週次時系列特徴量のシーケンスを抽出する

    Args:
        weekly_df: 週次特徴量DataFrame
        ticker: ティッカー
        end_date: 終了日（この日までのデータを使用）
        n_weeks: 抽出する週数

    Returns:
        (n_weeks, 23) のnumpy配列、またはNone（データ不足の場合）
    """
    feature_cols = get_weekly_feature_columns()

    ticker_df = weekly_df[
        (weekly_df["Ticker"] == ticker) &
        (weekly_df["Date"] <= end_date)
    ].copy()

    if len(ticker_df) < n_weeks:
        return None

    # 最新n_weeks分を取得
    ticker_df = ticker_df.tail(n_weeks)

    # 特徴量のみ抽出
    features = ticker_df[feature_cols].values

    # NaN/Infをチェック
    if np.any(~np.isfinite(features)):
        # NaNを0で埋める（初期の週でMA等が計算できない場合）
        features = np.nan_to_num(features, nan=0.0, posinf=0.0, neginf=0.0)

    return features.astype(np.float32)
