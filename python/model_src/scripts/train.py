# python/model_src/scripts/train.py

import pytorch_lightning as pl
from model_src.datamodules.stock_datamodule import StockDataModule
from model_src.lit_modules.lit_model import LitStockModel
import torch

def main():
    # データ準備
    data_module = StockDataModule(
        data_path='data/raw/6758.T_merged.csv',  # 学習用CSVのパス
        seq_len=30,
        batch_size=64
    )
    data_module.prepare_data()
    data_module.setup()

    # 特徴量数を取得（DataLoader の 1 バッチ目から）
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

    # Trainer のセットアップ
    trainer = pl.Trainer(
        max_epochs=20,
        accelerator='auto',
        log_every_n_steps=10
    )

    # 学習開始
    trainer.fit(model, data_module)

if __name__ == '__main__':
    main()
