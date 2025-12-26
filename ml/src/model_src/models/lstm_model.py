# ml/src/model_src/models/lstm_model.py

"""
株価予測用LSTMモデル

仕様書に基づくモデルアーキテクチャ:
1. 週次時系列特徴量 (batch, 156, 23) → LSTM/BiLSTM
2. セクターID → Embedding
3. [LSTM出力, 静的特徴量, 位置情報, SectorEmb] を結合
4. MLP Head → 12ヶ月対数リターン予測
"""

from __future__ import annotations
from typing import Dict, Optional

import torch
import torch.nn as nn


class StockPredictionLSTM(nn.Module):
    """
    株価予測用LSTMモデル

    入力:
        - weekly_seq: (batch, 156, 23) 週次時系列特徴量
        - static_features: (batch, 6) 静的特徴量
        - position_features: (batch, 2) 位置情報特徴量
        - sector_id: (batch,) セクターID

    出力:
        - prediction: (batch, 12) 1~12ヶ月対数リターン予測値
    """

    def __init__(
        self,
        # LSTM設定
        lstm_input_size: int = 23,
        lstm_hidden_size: int = 128,
        lstm_num_layers: int = 2,
        lstm_dropout: float = 0.2,
        use_bidirectional: bool = True,
        # Embedding設定
        num_sectors: int = 10,
        sector_embedding_dim: int = 8,
        # 静的特徴量
        static_feature_size: int = 6,
        position_feature_size: int = 2,
        # MLP Head設定
        mlp_hidden_sizes: list[int] = None,
        mlp_dropout: float = 0.3,
        # その他
        use_batch_norm: bool = True,
    ):
        """
        Args:
            lstm_input_size: LSTM入力次元（週次特徴量数）
            lstm_hidden_size: LSTM隠れ層次元
            lstm_num_layers: LSTMレイヤー数
            lstm_dropout: LSTM Dropout率
            use_bidirectional: BiLSTMを使用するか
            num_sectors: セクター数
            sector_embedding_dim: セクターEmbedding次元
            static_feature_size: 静的特徴量次元
            position_feature_size: 位置情報特徴量次元
            mlp_hidden_sizes: MLP Headの隠れ層サイズリスト
            mlp_dropout: MLP Dropout率
            use_batch_norm: Batch Normalizationを使用するか
        """
        super().__init__()

        self.lstm_hidden_size = lstm_hidden_size
        self.use_bidirectional = use_bidirectional

        # LSTM層
        self.lstm = nn.LSTM(
            input_size=lstm_input_size,
            hidden_size=lstm_hidden_size,
            num_layers=lstm_num_layers,
            dropout=lstm_dropout if lstm_num_layers > 1 else 0.0,
            bidirectional=use_bidirectional,
            batch_first=True,
        )

        # セクターEmbedding
        self.sector_embedding = nn.Embedding(
            num_embeddings=num_sectors,
            embedding_dim=sector_embedding_dim,
        )

        # LSTM出力次元（BiLSTMの場合は2倍）
        lstm_output_size = lstm_hidden_size * (2 if use_bidirectional else 1)

        # 結合後の特徴量次元
        combined_size = (
            lstm_output_size +
            sector_embedding_dim +
            static_feature_size +
            position_feature_size
        )

        # MLP Head（デフォルト: [256, 128, 64]）
        if mlp_hidden_sizes is None:
            mlp_hidden_sizes = [256, 128, 64]

        # MLP層の構築
        mlp_layers = []
        prev_size = combined_size

        for hidden_size in mlp_hidden_sizes:
            mlp_layers.append(nn.Linear(prev_size, hidden_size))
            if use_batch_norm:
                mlp_layers.append(nn.BatchNorm1d(hidden_size))
            mlp_layers.append(nn.ReLU())
            mlp_layers.append(nn.Dropout(mlp_dropout))
            prev_size = hidden_size

        # 最終出力層（12次元：1~12ヶ月対数リターン）
        mlp_layers.append(nn.Linear(prev_size, 12))

        self.mlp_head = nn.Sequential(*mlp_layers)

    def forward(
        self,
        weekly_seq: torch.Tensor,
        static_features: torch.Tensor,
        position_features: torch.Tensor,
        sector_id: torch.Tensor,
    ) -> torch.Tensor:
        """
        順伝播

        Args:
            weekly_seq: (batch, 156, 23) 週次時系列特徴量
            static_features: (batch, 6) 静的特徴量
            position_features: (batch, 2) 位置情報特徴量
            sector_id: (batch,) セクターID

        Returns:
            prediction: (batch, 12) 1~12ヶ月対数リターン予測値
        """
        batch_size = weekly_seq.size(0)

        # 1. LSTM処理
        # lstm_out: (batch, 156, lstm_hidden_size * 2)
        # hidden: (num_layers * 2, batch, lstm_hidden_size)
        lstm_out, (hidden, cell) = self.lstm(weekly_seq)

        # 最終時刻の出力を取得
        # lstm_last: (batch, lstm_hidden_size * 2)
        lstm_last = lstm_out[:, -1, :]

        # 2. セクターEmbedding
        # sector_emb: (batch, sector_embedding_dim)
        sector_emb = self.sector_embedding(sector_id)

        # 3. 全特徴量を結合
        # combined: (batch, lstm_output_size + sector_emb_dim + 6 + 2)
        combined = torch.cat([
            lstm_last,
            sector_emb,
            static_features,
            position_features,
        ], dim=1)

        # 4. MLP Head
        # output: (batch, 12)
        prediction = self.mlp_head(combined)

        return prediction

    def get_lstm_features(
        self,
        weekly_seq: torch.Tensor,
    ) -> torch.Tensor:
        """
        LSTM特徴量のみを取得（可視化・分析用）

        Args:
            weekly_seq: (batch, 156, 23)

        Returns:
            lstm_features: (batch, lstm_hidden_size * 2)
        """
        with torch.no_grad():
            lstm_out, _ = self.lstm(weekly_seq)
            lstm_last = lstm_out[:, -1, :]
        return lstm_last


class StockPredictionLSTMWithAttention(nn.Module):
    """
    Attention機構付きLSTMモデル（オプション）

    標準LSTMモデルの拡張版。
    週次時系列の各時点に異なる重みを付けることで、
    より重要な時期に焦点を当てた予測を行う。
    """

    def __init__(
        self,
        # LSTM設定
        lstm_input_size: int = 23,
        lstm_hidden_size: int = 128,
        lstm_num_layers: int = 2,
        lstm_dropout: float = 0.2,
        use_bidirectional: bool = True,
        # Attention設定
        attention_dim: int = 64,
        # Embedding設定
        num_sectors: int = 10,
        sector_embedding_dim: int = 8,
        # 静的特徴量
        static_feature_size: int = 6,
        position_feature_size: int = 2,
        # MLP Head設定
        mlp_hidden_sizes: list[int] = None,
        mlp_dropout: float = 0.3,
        # その他
        use_batch_norm: bool = True,
    ):
        super().__init__()

        self.lstm_hidden_size = lstm_hidden_size
        self.use_bidirectional = use_bidirectional

        # LSTM層
        self.lstm = nn.LSTM(
            input_size=lstm_input_size,
            hidden_size=lstm_hidden_size,
            num_layers=lstm_num_layers,
            dropout=lstm_dropout if lstm_num_layers > 1 else 0.0,
            bidirectional=use_bidirectional,
            batch_first=True,
        )

        # Attention機構
        lstm_output_size = lstm_hidden_size * (2 if use_bidirectional else 1)
        self.attention = nn.Sequential(
            nn.Linear(lstm_output_size, attention_dim),
            nn.Tanh(),
            nn.Linear(attention_dim, 1),
        )

        # セクターEmbedding
        self.sector_embedding = nn.Embedding(
            num_embeddings=num_sectors,
            embedding_dim=sector_embedding_dim,
        )

        # 結合後の特徴量次元
        combined_size = (
            lstm_output_size +
            sector_embedding_dim +
            static_feature_size +
            position_feature_size
        )

        # MLP Head
        if mlp_hidden_sizes is None:
            mlp_hidden_sizes = [256, 128, 64]

        mlp_layers = []
        prev_size = combined_size

        for hidden_size in mlp_hidden_sizes:
            mlp_layers.append(nn.Linear(prev_size, hidden_size))
            if use_batch_norm:
                mlp_layers.append(nn.BatchNorm1d(hidden_size))
            mlp_layers.append(nn.ReLU())
            mlp_layers.append(nn.Dropout(mlp_dropout))
            prev_size = hidden_size

        mlp_layers.append(nn.Linear(prev_size, 12))

        self.mlp_head = nn.Sequential(*mlp_layers)

    def forward(
        self,
        weekly_seq: torch.Tensor,
        static_features: torch.Tensor,
        position_features: torch.Tensor,
        sector_id: torch.Tensor,
    ) -> torch.Tensor:
        """
        順伝播（Attention付き）

        Args:
            weekly_seq: (batch, 156, 23)
            static_features: (batch, 6)
            position_features: (batch, 2)
            sector_id: (batch,)

        Returns:
            prediction: (batch, 12)
        """
        # 1. LSTM処理
        # lstm_out: (batch, 156, lstm_hidden_size * 2)
        lstm_out, _ = self.lstm(weekly_seq)

        # 2. Attention重み計算
        # attention_scores: (batch, 156, 1)
        attention_scores = self.attention(lstm_out)
        # attention_weights: (batch, 156, 1)
        attention_weights = torch.softmax(attention_scores, dim=1)

        # 3. 重み付き和
        # weighted_lstm: (batch, lstm_hidden_size * 2)
        weighted_lstm = torch.sum(lstm_out * attention_weights, dim=1)

        # 4. セクターEmbedding
        sector_emb = self.sector_embedding(sector_id)

        # 5. 全特徴量を結合
        combined = torch.cat([
            weighted_lstm,
            sector_emb,
            static_features,
            position_features,
        ], dim=1)

        # 6. MLP Head
        prediction = self.mlp_head(combined)

        return prediction

    def get_attention_weights(
        self,
        weekly_seq: torch.Tensor,
    ) -> torch.Tensor:
        """
        Attention重みを取得（可視化用）

        Args:
            weekly_seq: (batch, 156, 23)

        Returns:
            attention_weights: (batch, 156)
        """
        with torch.no_grad():
            lstm_out, _ = self.lstm(weekly_seq)
            attention_scores = self.attention(lstm_out)
            attention_weights = torch.softmax(attention_scores, dim=1)
        return attention_weights.squeeze(2)
