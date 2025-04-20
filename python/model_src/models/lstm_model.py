# python/model_src/models/lstm_model.py

import torch
import torch.nn as nn

class StockLSTM(nn.Module):
    """
    LSTMベースの株価予測モデル
    入力された時系列特徴量から、次の7営業日の終値を予測する

    Args:
        input_size (int): 入力特徴量の次元
        hidden_size (int): LSTMの隠れ状態の次元
        num_layers (int): LSTMのレイヤー数
        dropout (float): ドロップアウト率
        output_size (int): 出力次元（デフォルト: 7）
    """
    def __init__(self,
                 input_size: int,
                 hidden_size: int = 64,
                 num_layers: int = 2,
                 dropout: float = 0.2,
                 output_size: int = 7):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout
        )
        self.fc = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        """
        Args:
            x (torch.Tensor): 入力テンソル（shape: [batch_size, seq_len, input_size]）

        Returns:
            torch.Tensor: 出力テンソル（shape: [batch_size, 7]）
        """
        out, _ = self.lstm(x)  # shape: [batch, seq_len, hidden_size]
        last = out[:, -1, :]   # shape: [batch, hidden_size]
        return self.fc(last)   # shape: [batch, output_size]