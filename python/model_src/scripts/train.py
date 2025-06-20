# python/model_src/scripts/train.py

import pytorch_lightning as pl
from pytorch_lightning.callbacks import ModelCheckpoint
from model_src.datamodules.lstm_datamodule import LSTMDataModule
from model_src.lit_modules.lit_model import LitStockModel
import torch
import os

def main():
    # データ準備
    data_module = LSTMDataModule(
        data_dir='data/raw/',  # 銘柄ごとのCSVファイルが保存されているディレクトリ
        seq_len=30,
        batch_size=64
    )
    data_module.prepare_data()
    data_module.setup()

    # 特徴量数を取得
    sample_batch = next(iter(data_module.train_dataloader()))
    input_size = sample_batch[0].shape[-1]

    # モデル構築
    model = LitStockModel(
        input_size=input_size,
        hidden_size=64,
        num_layers=2,
        dropout=0.2,
        lr=1e-3
    )

    # チェックポイントコールバック設定
    checkpoint_callback = ModelCheckpoint(
        monitor="val_loss",      # val_loss が最小になったとき保存
        dirpath="checkpoints/",  # 保存先ディレクトリ
        filename="best_model",   # ファイル名
        save_top_k=1,            # 最も良かったモデルだけ保存
        mode="min"               # val_loss を最小化する
    )

    # Trainerセットアップ
    trainer = pl.Trainer(
        max_epochs=30,
        accelerator='auto',
        callbacks=[checkpoint_callback],
        log_every_n_steps=10,
        deterministic=True
    )

    # 学習開始
    trainer.fit(model, data_module)

if __name__ == '__main__':
    os.makedirs("checkpoints/", exist_ok=True)  # 保存先ディレクトリを作成しておく
    main()
