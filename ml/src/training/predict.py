# python/model_src/scripts/predict.py

import torch
import pandas as pd
from model_src.lit_modules.lit_model import LitStockModel
from model_src.datamodules.lstm_datamodule import LSTMDataModule
import os

def predict_future(data_dir: str, checkpoint_path: str, output_path: str = "predictions.csv"):
    """
    保存されたモデルを使って未来7営業日の株価を予測し、CSVに保存

    Args:
        data_dir (str): データフォルダのパス（学習時と同様に銘柄CSVが置いてあるディレクトリ）
        checkpoint_path (str): 学習済みモデルのチェックポイントファイルパス
        output_path (str): 予測結果を保存するCSVファイルパス（デフォルト: 'predictions.csv'）

    Returns:
        None
    """
    # DataModule のセットアップ
    datamodule = LSTMDataModule(
        data_dir=data_dir,
        seq_len=30,
        batch_size=1,
        num_workers=0
    )
    datamodule.prepare_data()
    datamodule.setup()

    # 特徴量数を取得
    sample_batch = next(iter(datamodule.val_dataloader()))
    input_size = sample_batch[0].shape[-1]

    # モデル読み込み
    model = LitStockModel.load_from_checkpoint(checkpoint_path, input_size=input_size)
    model.eval()

    preds = []
    tickers = []

    # 予測実行
    for x_batch, _ in datamodule.val_dataloader():
        with torch.no_grad():
            y_pred = model(x_batch)
            preds.append(y_pred.squeeze(0).cpu().numpy())

    # Tickerを対応させる
    df_val = datamodule.df.iloc[int(len(datamodule.df)*0.8):].copy()
    tickers = df_val['Ticker'].iloc[datamodule.val_dataset.valid_idx[:len(preds)]].tolist()

    # DataFrame化
    results = pd.DataFrame(preds, columns=[f"Day{i+1}" for i in range(7)])
    results['Ticker'] = tickers

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    results.to_csv(output_path, index=False)
    print(f"prediction result is saved in {output_path}")

if __name__ == '__main__':
    predict_future(
        data_dir='data/raw/',
        checkpoint_path='checkpoints/best_model.ckpt',
        output_path='predictions/predictions.csv'
    )
