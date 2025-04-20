# python/model_src/lit_modules/lit_model.py

import sys
from pathlib import Path
import torch
import torch.nn.functional as F
import pytorch_lightning as pl

repo_dir = Path(__file__).absolute().parents[3]
sys.path.append(repo_dir.as_posix())

from model_src.models.lstm_model import StockLSTM

class LitStockModel(pl.LightningModule):
    """
    PyTorch Lightning モデルラッパー。

    StockLSTM モデルを使用し、学習・検証ロジックを定義。

    Args:
        input_size (int): 入力特徴量の次元
        hidden_size (int): LSTM の隠れ状態サイズ
        num_layers (int): LSTM レイヤー数
        dropout (float): ドロップアウト率
        lr (float): 学習率
    """
    def __init__(self,
                 input_size: int,
                 hidden_size: int = 64,
                 num_layers: int = 2,
                 dropout: float = 0.2,
                 lr: float = 1e-3):
        super().__init__()
        self.save_hyperparameters()
        self.model = StockLSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout,
            output_size=7
        )

    def forward(self, x):
        return self.model(x)

    def training_step(self, batch, batch_idx):
        x, y = batch  # y: [batch_size, 7]
        y_hat = self(x)  # [batch_size, 7]
        loss = F.mse_loss(y_hat, y)
        self.log("train_loss", loss)
        return loss

    def validation_step(self, batch, batch_idx):
        x, y = batch
        y_hat = self(x)
        loss = F.mse_loss(y_hat, y)
        self.log("val_loss", loss, prog_bar=True)

    def configure_optimizers(self):
        return torch.optim.Adam(self.parameters(), lr=self.hparams.lr)
