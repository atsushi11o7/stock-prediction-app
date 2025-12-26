# ml/src/model_src/lit_modules/lit_model.py

"""
株価予測用PyTorch Lightning Module

モデルの学習・検証・テスト・推論ロジックをカプセル化。
"""

from __future__ import annotations
from typing import Dict, Any, Optional
from pathlib import Path
import sys

import torch
import torch.nn as nn
import pytorch_lightning as pl

# モデルのインポート
script_dir = Path(__file__).resolve().parent.parent.parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

from model_src.models.lstm_model import StockPredictionLSTM, StockPredictionLSTMWithAttention


class StockPredictionLitModule(pl.LightningModule):
    """
    株価予測用PyTorch Lightning Module

    機能:
    - 学習ループ（MSE損失）
    - 検証ループ
    - テストループ
    - オプティマイザ設定
    - 学習率スケジューラ設定
    - メトリクス計算（MSE, MAE, 方向精度）
    """

    def __init__(
        self,
        # モデル設定
        model_type: str = "lstm",  # "lstm" or "lstm_attention"
        lstm_hidden_size: int = 128,
        lstm_num_layers: int = 2,
        lstm_dropout: float = 0.2,
        use_bidirectional: bool = True,
        num_sectors: int = 10,
        sector_embedding_dim: int = 8,
        mlp_hidden_sizes: list[int] = None,
        mlp_dropout: float = 0.3,
        use_batch_norm: bool = True,
        # Attention設定（model_type="lstm_attention"の場合のみ）
        attention_dim: int = 64,
        # 最適化設定
        learning_rate: float = 1e-3,
        weight_decay: float = 1e-5,
        # スケジューラ設定
        use_scheduler: bool = True,
        scheduler_type: str = "reduce_on_plateau",  # "reduce_on_plateau" or "cosine"
        scheduler_patience: int = 10,
        scheduler_factor: float = 0.5,
        # その他
        log_predictions: bool = False,
    ):
        """
        Args:
            model_type: モデルタイプ（"lstm" or "lstm_attention"）
            lstm_hidden_size: LSTM隠れ層次元
            lstm_num_layers: LSTMレイヤー数
            lstm_dropout: LSTM Dropout率
            use_bidirectional: BiLSTMを使用するか
            num_sectors: セクター数
            sector_embedding_dim: セクターEmbedding次元
            mlp_hidden_sizes: MLP Headの隠れ層サイズリスト
            mlp_dropout: MLP Dropout率
            use_batch_norm: Batch Normalizationを使用するか
            attention_dim: Attention次元（lstm_attentionの場合）
            learning_rate: 学習率
            weight_decay: Weight Decay
            use_scheduler: スケジューラを使用するか
            scheduler_type: スケジューラタイプ
            scheduler_patience: ReduceLROnPlateauのpatience
            scheduler_factor: ReduceLROnPlateauのfactor
            log_predictions: 予測値をログに記録するか
        """
        super().__init__()

        # ハイパーパラメータを保存
        self.save_hyperparameters()

        # モデルの構築
        model_kwargs = {
            "lstm_input_size": 23,
            "lstm_hidden_size": lstm_hidden_size,
            "lstm_num_layers": lstm_num_layers,
            "lstm_dropout": lstm_dropout,
            "use_bidirectional": use_bidirectional,
            "num_sectors": num_sectors,
            "sector_embedding_dim": sector_embedding_dim,
            "static_feature_size": 6,
            "position_feature_size": 2,
            "mlp_hidden_sizes": mlp_hidden_sizes,
            "mlp_dropout": mlp_dropout,
            "use_batch_norm": use_batch_norm,
        }

        if model_type == "lstm_attention":
            model_kwargs["attention_dim"] = attention_dim
            self.model = StockPredictionLSTMWithAttention(**model_kwargs)
        else:
            self.model = StockPredictionLSTM(**model_kwargs)

        # 損失関数
        self.criterion = nn.MSELoss()

        # メトリクス保存用
        self.train_losses = []
        self.val_losses = []

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
            weekly_seq: (batch, 156, 23)
            static_features: (batch, 6)
            position_features: (batch, 2)
            sector_id: (batch,)

        Returns:
            prediction: (batch,)
        """
        return self.model(
            weekly_seq=weekly_seq,
            static_features=static_features,
            position_features=position_features,
            sector_id=sector_id,
        )

    def training_step(self, batch: Dict[str, torch.Tensor], batch_idx: int) -> torch.Tensor:
        """
        学習ステップ

        Args:
            batch: DataLoaderから取得したバッチ
            batch_idx: バッチインデックス

        Returns:
            loss: 損失値
        """
        # 予測
        predictions = self(
            weekly_seq=batch["weekly_seq"],
            static_features=batch["static_features"],
            position_features=batch["position_features"],
            sector_id=batch["sector_id"],
        )

        # 損失計算
        targets = batch["target"]
        loss = self.criterion(predictions, targets)

        # メトリクス計算
        mae = torch.mean(torch.abs(predictions - targets))

        # 方向精度（上昇/下落の予測が正しいか）
        direction_correct = ((predictions > 0) == (targets > 0)).float().mean()

        # ログ記録
        self.log("train_loss", loss, on_step=True, on_epoch=True, prog_bar=True)
        self.log("train_mae", mae, on_step=False, on_epoch=True)
        self.log("train_direction_acc", direction_correct, on_step=False, on_epoch=True)

        return loss

    def validation_step(self, batch: Dict[str, torch.Tensor], batch_idx: int) -> torch.Tensor:
        """
        検証ステップ

        Args:
            batch: DataLoaderから取得したバッチ
            batch_idx: バッチインデックス

        Returns:
            loss: 損失値
        """
        # 予測
        predictions = self(
            weekly_seq=batch["weekly_seq"],
            static_features=batch["static_features"],
            position_features=batch["position_features"],
            sector_id=batch["sector_id"],
        )

        # 損失計算
        targets = batch["target"]
        loss = self.criterion(predictions, targets)

        # メトリクス計算
        mae = torch.mean(torch.abs(predictions - targets))
        direction_correct = ((predictions > 0) == (targets > 0)).float().mean()

        # ログ記録
        self.log("val_loss", loss, on_step=False, on_epoch=True, prog_bar=True)
        self.log("val_mae", mae, on_step=False, on_epoch=True)
        self.log("val_direction_acc", direction_correct, on_step=False, on_epoch=True)

        return loss

    def test_step(self, batch: Dict[str, torch.Tensor], batch_idx: int) -> Dict[str, torch.Tensor]:
        """
        テストステップ

        Args:
            batch: DataLoaderから取得したバッチ
            batch_idx: バッチインデックス

        Returns:
            metrics: メトリクスの辞書
        """
        # 予測
        predictions = self(
            weekly_seq=batch["weekly_seq"],
            static_features=batch["static_features"],
            position_features=batch["position_features"],
            sector_id=batch["sector_id"],
        )

        # 損失計算
        targets = batch["target"]
        loss = self.criterion(predictions, targets)

        # メトリクス計算
        mae = torch.mean(torch.abs(predictions - targets))
        direction_correct = ((predictions > 0) == (targets > 0)).float().mean()

        # RMSE
        rmse = torch.sqrt(loss)

        # ログ記録
        self.log("test_loss", loss, on_step=False, on_epoch=True)
        self.log("test_mae", mae, on_step=False, on_epoch=True)
        self.log("test_rmse", rmse, on_step=False, on_epoch=True)
        self.log("test_direction_acc", direction_correct, on_step=False, on_epoch=True)

        return {
            "loss": loss,
            "mae": mae,
            "rmse": rmse,
            "direction_acc": direction_correct,
            "predictions": predictions,
            "targets": targets,
        }

    def predict_step(
        self,
        batch: Dict[str, torch.Tensor],
        batch_idx: int,
    ) -> Dict[str, torch.Tensor]:
        """
        推論ステップ

        Args:
            batch: DataLoaderから取得したバッチ
            batch_idx: バッチインデックス

        Returns:
            predictions: 予測結果の辞書
        """
        # 予測
        predictions = self(
            weekly_seq=batch["weekly_seq"],
            static_features=batch["static_features"],
            position_features=batch["position_features"],
            sector_id=batch["sector_id"],
        )

        return {
            "predictions": predictions,
            "weekly_seq": batch["weekly_seq"],
            "static_features": batch["static_features"],
            "position_features": batch["position_features"],
            "sector_id": batch["sector_id"],
        }

    def configure_optimizers(self) -> Dict[str, Any]:
        """
        オプティマイザとスケジューラの設定

        Returns:
            optimizer_config: オプティマイザ設定の辞書
        """
        # オプティマイザ
        optimizer = torch.optim.AdamW(
            self.parameters(),
            lr=self.hparams.learning_rate,
            weight_decay=self.hparams.weight_decay,
        )

        if not self.hparams.use_scheduler:
            return optimizer

        # スケジューラ
        if self.hparams.scheduler_type == "reduce_on_plateau":
            scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
                optimizer,
                mode="min",
                factor=self.hparams.scheduler_factor,
                patience=self.hparams.scheduler_patience,
            )

            return {
                "optimizer": optimizer,
                "lr_scheduler": {
                    "scheduler": scheduler,
                    "monitor": "val_loss",
                    "frequency": 1,
                },
            }

        elif self.hparams.scheduler_type == "cosine":
            scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
                optimizer,
                T_max=100,
                eta_min=1e-6,
            )

            return {
                "optimizer": optimizer,
                "lr_scheduler": scheduler,
            }

        else:
            return optimizer

    def on_train_epoch_end(self) -> None:
        """学習エポック終了時の処理"""
        # 現在の学習率をログ
        current_lr = self.optimizers().param_groups[0]["lr"]
        self.log("learning_rate", current_lr, on_epoch=True)

    def convert_log_return_to_price(
        self,
        current_price: torch.Tensor,
        log_return: torch.Tensor,
    ) -> torch.Tensor:
        """
        対数リターンから12ヶ月後の株価を計算

        Args:
            current_price: 現在の株価 (batch,)
            log_return: 予測された12ヶ月対数リターン (batch,)

        Returns:
            predicted_price: 予測株価 (batch,)
        """
        return current_price * torch.exp(log_return)

    def get_model_summary(self) -> str:
        """
        モデルのサマリを取得

        Returns:
            summary: モデルサマリ文字列
        """
        total_params = sum(p.numel() for p in self.parameters())
        trainable_params = sum(p.numel() for p in self.parameters() if p.requires_grad)

        summary = f"""
Stock Prediction LSTM Model Summary
{'=' * 60}
Model Type: {self.hparams.model_type}
LSTM Hidden Size: {self.hparams.lstm_hidden_size}
LSTM Num Layers: {self.hparams.lstm_num_layers}
Use Bidirectional: {self.hparams.use_bidirectional}
MLP Hidden Sizes: {self.hparams.mlp_hidden_sizes}
Sector Embedding Dim: {self.hparams.sector_embedding_dim}
{'=' * 60}
Total Parameters: {total_params:,}
Trainable Parameters: {trainable_params:,}
{'=' * 60}
"""
        return summary
