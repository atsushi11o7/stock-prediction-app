import torch
import pandas as pd
import matplotlib.pyplot as plt
import os

def plot_predictions(df: pd.DataFrame):
    """
    予測結果を銘柄ごとに7日間プロット

    Args:
        df (pd.DataFrame): 予測結果データフレーム

    Returns:
        None
    """
    os.makedirs("data/plots/", exist_ok=True)

    for ticker in df['Ticker'].unique():
        sub_df = df[df['Ticker'] == ticker]
        if sub_df.empty:
            continue
        y = sub_df.iloc[0][[f"Day{i+1}" for i in range(7)]].values

        plt.figure()
        plt.plot(range(1, 8), y, marker='o')
        plt.title(f"Predicted 7-Day Stock Prices for {ticker}")
        plt.xlabel("Days Ahead")
        plt.ylabel("Predicted Close Price")
        plt.grid(True)
        plt.savefig(f"plots/{ticker}_prediction.png")
        plt.close()

def plot_predictions_with_actual(df_pred: pd.DataFrame, df_val: pd.DataFrame, val_dataset):
    """
    実測株価と予測株価を比較するグラフを作成・保存

    Args:
        df_pred (pd.DataFrame): 予測結果データフレーム
        df_val (pd.DataFrame): バリデーション用の実際の株価データ
        val_dataset (Dataset): Validation データセット（valid_idxを使う）
    """
    os.makedirs("plots/", exist_ok=True)

    for ticker in df_pred['Ticker'].unique():
        sub_pred = df_pred[df_pred['Ticker'] == ticker]
        if sub_pred.empty:
            continue

        y_pred = sub_pred.iloc[0][[f"Day{i+1}" for i in range(7)]].values

        # 実測株価（直近7営業日分）を取得
        ticker_val = df_val[df_val['Ticker'] == ticker]
        if ticker_val.empty:
            continue

        idx = val_dataset.valid_idx[df_pred.index.get_loc(sub_pred.index[0])]
        recent_actual = ticker_val['Close'].iloc[idx-6:idx+1].values  # 最新7日分

        if len(recent_actual) < 7:
            continue

        # プロット
        plt.figure()
        plt.plot(range(-6, 1), recent_actual, label='Actual (Past 7 Days)', marker='o')
        plt.plot(range(1, 8), y_pred, label='Predicted (Next 7 Days)', marker='x')
        plt.title(f"Stock Prediction vs Actual for {ticker}")
        plt.xlabel("Days (0 = Today)")
        plt.ylabel("Close Price")
        plt.axvline(x=0, color='black', linestyle='--')  # 境界線
        plt.legend()
        plt.grid(True)
        plt.savefig(f"plots/{ticker}_compare.png")
        plt.close()