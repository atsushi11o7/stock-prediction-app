# ml/src/training/utils/onnx_export.py

"""
ONNX モデルエクスポート用ユーティリティ

PyTorch Lightning モデルおよび純粋な PyTorch モデルの両方に対応。
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, Optional, Union
import json
import logging

import torch
import torch.nn as nn

# PyTorch Lightning はオプショナル
try:
    import pytorch_lightning as pl
    HAS_LIGHTNING = True
except ImportError:
    HAS_LIGHTNING = False
    pl = None

# 定数をインポート
import sys
script_dir = Path(__file__).resolve().parent.parent.parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

from common.constants import (
    N_WEEKS_INPUT,
    N_WEEKLY_FEATURES,
    N_STATIC_FEATURES,
    N_POSITION_FEATURES,
    DEFAULT_ONNX_OPSET_VERSION,
    ONNX_DYNAMIC_AXES,
    ONNX_INPUT_NAMES,
    ONNX_OUTPUT_NAMES,
)

logger = logging.getLogger(__name__)


class PathEncoder(json.JSONEncoder):
    """PosixPath などの Path オブジェクトをJSON化するためのエンコーダー"""
    def default(self, obj):
        if isinstance(obj, Path):
            return str(obj)
        return super().default(obj)


def export_pytorch_model_to_onnx(
    model: nn.Module,
    output_path: Path,
    opset_version: int = DEFAULT_ONNX_OPSET_VERSION,
    num_sectors: int = 9,
) -> None:
    """
    純粋な PyTorch モデルをONNXにエクスポート

    Args:
        model: PyTorch モデル (nn.Module)
        output_path: 出力パス
        opset_version: ONNX opset バージョン
        num_sectors: セクター数（ダミー入力用）
    """
    model = model.cpu()
    model.eval()

    # ダミー入力データ
    batch_size = 1
    dummy_weekly_seq = torch.randn(batch_size, N_WEEKS_INPUT, N_WEEKLY_FEATURES)
    dummy_static_features = torch.randn(batch_size, N_STATIC_FEATURES)
    dummy_position_features = torch.randn(batch_size, N_POSITION_FEATURES)
    dummy_sector_id = torch.randint(0, num_sectors, (batch_size,))

    # ONNX エクスポート
    torch.onnx.export(
        model,
        (
            dummy_weekly_seq,
            dummy_static_features,
            dummy_position_features,
            dummy_sector_id,
        ),
        output_path,
        export_params=True,
        opset_version=opset_version,
        do_constant_folding=True,
        input_names=ONNX_INPUT_NAMES,
        output_names=ONNX_OUTPUT_NAMES,
        dynamic_axes=ONNX_DYNAMIC_AXES,
    )

    logger.info(f"ONNX model exported to: {output_path}")


def export_to_onnx(
    model: Union[nn.Module, "pl.LightningModule"],
    output_path: Path,
    opset_version: int = DEFAULT_ONNX_OPSET_VERSION,
    dynamic_axes: Optional[Dict[str, Dict[int, str]]] = None,
    num_sectors: int = 9,
) -> None:
    """
    PyTorch / PyTorch Lightning モデルをONNXにエクスポート（統一インターフェース）

    Args:
        model: PyTorch モデル (nn.Module) または PyTorch Lightning モデル
        output_path: 出力パス
        opset_version: ONNX opset バージョン
        dynamic_axes: 動的軸の設定（省略時はデフォルト値を使用）
        num_sectors: セクター数（ダミー入力用）
    """
    # ONNXエクスポートはCPUで行う
    model = model.cpu()
    model.eval()

    # ダミー入力データ（CPU上に作成）
    batch_size = 1
    dummy_weekly_seq = torch.randn(batch_size, N_WEEKS_INPUT, N_WEEKLY_FEATURES)
    dummy_static_features = torch.randn(batch_size, N_STATIC_FEATURES)
    dummy_position_features = torch.randn(batch_size, N_POSITION_FEATURES)
    dummy_sector_id = torch.randint(0, num_sectors, (batch_size,))

    # デフォルトの動的軸設定
    if dynamic_axes is None:
        dynamic_axes = ONNX_DYNAMIC_AXES

    # PyTorch Lightning モデルか純粋な PyTorch モデルかを判定
    if HAS_LIGHTNING and isinstance(model, pl.LightningModule):
        # Lightning モデルの場合は内部モデルを使用
        pytorch_model = model.model
    else:
        # 純粋な PyTorch モデル
        pytorch_model = model

    # ONNX エクスポート
    torch.onnx.export(
        pytorch_model,
        (
            dummy_weekly_seq,
            dummy_static_features,
            dummy_position_features,
            dummy_sector_id,
        ),
        output_path,
        export_params=True,
        opset_version=opset_version,
        do_constant_folding=True,
        input_names=ONNX_INPUT_NAMES,
        output_names=ONNX_OUTPUT_NAMES,
        dynamic_axes=dynamic_axes,
    )

    logger.info(f"ONNX model exported to: {output_path}")


def verify_onnx_model(
    onnx_path: Path,
    pytorch_model: pl.LightningModule,
) -> bool:
    """
    ONNXモデルの検証

    Args:
        onnx_path: ONNXモデルのパス
        pytorch_model: 元のPyTorchモデル

    Returns:
        verification_passed: 検証が成功したか
    """
    try:
        import onnx
        import onnxruntime as ort
        import numpy as np

        # ONNX モデルの読み込みと検証
        onnx_model = onnx.load(str(onnx_path))
        onnx.checker.check_model(onnx_model)
        print("[OK] ONNX model structure is valid")

        # ONNX Runtime セッションの作成
        ort_session = ort.InferenceSession(str(onnx_path))

        # テスト入力データ
        batch_size = 2
        weekly_seq = torch.randn(batch_size, 156, 23)
        static_features = torch.randn(batch_size, 6)
        position_features = torch.randn(batch_size, 2)
        sector_id = torch.randint(0, 9, (batch_size,))

        # PyTorch モデルで推論
        pytorch_model.eval()
        with torch.no_grad():
            pytorch_output = pytorch_model(
                weekly_seq,
                static_features,
                position_features,
                sector_id,
            )

        # ONNX モデルで推論
        ort_inputs = {
            "weekly_seq": weekly_seq.numpy(),
            "static_features": static_features.numpy(),
            "position_features": position_features.numpy(),
            "sector_id": sector_id.numpy(),
        }
        ort_outputs = ort_session.run(None, ort_inputs)

        # 出力の比較
        pytorch_output_np = pytorch_output.numpy()
        onnx_output_np = ort_outputs[0]

        max_diff = np.abs(pytorch_output_np - onnx_output_np).max()
        print(f"[INFO] Max difference between PyTorch and ONNX: {max_diff:.6e}")

        if max_diff < 1e-5:
            print("[OK] ONNX model verification passed")
            return True
        else:
            print(f"[WARNING] ONNX model has differences > 1e-5: {max_diff}")
            return False

    except Exception as e:
        print(f"[ERROR] ONNX verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def save_model_metadata(
    output_path: Path,
    model: pl.LightningModule,
    sector_mapping: Dict[str, int],
    feature_columns: Dict[str, list],
    training_config: Dict[str, Any],
) -> None:
    """
    モデルのメタデータをJSONで保存

    Args:
        output_path: 出力パス
        model: PyTorch Lightning モデル
        sector_mapping: セクターマッピング
        feature_columns: 特徴量カラム情報
        training_config: 学習設定
    """
    metadata = {
        "model_type": model.hparams.model_type,
        "lstm_hidden_size": model.hparams.lstm_hidden_size,
        "lstm_num_layers": model.hparams.lstm_num_layers,
        "use_bidirectional": model.hparams.use_bidirectional,
        "sector_embedding_dim": model.hparams.sector_embedding_dim,
        "mlp_hidden_sizes": model.hparams.mlp_hidden_sizes,
        "num_parameters": sum(p.numel() for p in model.parameters()),
        "sector_mapping": sector_mapping,
        "feature_columns": feature_columns,
        "training_config": training_config,
        "input_spec": {
            "weekly_seq": {"shape": ["batch_size", 156, 23], "dtype": "float32"},
            "static_features": {"shape": ["batch_size", 6], "dtype": "float32"},
            "position_features": {"shape": ["batch_size", 2], "dtype": "float32"},
            "sector_id": {"shape": ["batch_size"], "dtype": "int64"},
        },
        "output_spec": {
            "prediction": {
                "shape": ["batch_size"],
                "dtype": "float32",
                "description": "12-month log return prediction",
            }
        },
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False, cls=PathEncoder)

    print(f"[OK] Model metadata saved to: {output_path}")
