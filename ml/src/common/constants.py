# ml/src/common/constants.py
"""
システム全体で使用する定数定義

マジックナンバーを集約し、保守性を向上させる。
"""

# =============================================================================
# モデル構造定数
# =============================================================================

# 週次時系列特徴量
N_WEEKS_INPUT = 156  # 入力週数（3年）
N_WEEKLY_FEATURES = 23  # 週次特徴量の数

# 静的特徴量
N_STATIC_FEATURES = 6  # 静的特徴量の数

# 位置特徴量
N_POSITION_FEATURES = 2  # 位置特徴量の数

# 出力
N_OUTPUT_MONTHS = 12  # 予測対象月数（1〜12ヶ月）

# =============================================================================
# データ処理定数
# =============================================================================

# 週次特徴量計算
WEEKS_PER_YEAR = 52
LOOKBACK_YEARS_DEFAULT = 3  # 静的特徴量計算のデフォルトlookback期間

# ファインチューニング用データ読み込み
FINETUNE_LOOKBACK_YEARS = 5  # ファインチューニング時のデータ読み込み期間

# 最小データ要件
MIN_DAILY_RECORDS_PER_TICKER = 200  # 銘柄あたりの最小日次レコード数

# =============================================================================
# デフォルトモデルハイパーパラメータ
# =============================================================================

DEFAULT_LSTM_HIDDEN_SIZE = 128
DEFAULT_LSTM_NUM_LAYERS = 2
DEFAULT_LSTM_DROPOUT = 0.2
DEFAULT_USE_BIDIRECTIONAL = True

DEFAULT_SECTOR_EMBEDDING_DIM = 8

DEFAULT_MLP_HIDDEN_SIZES = [256, 128, 64]
DEFAULT_MLP_DROPOUT = 0.3
DEFAULT_USE_BATCH_NORM = True

# =============================================================================
# ONNX設定
# =============================================================================

DEFAULT_ONNX_OPSET_VERSION = 14

# ONNX動的軸設定
ONNX_DYNAMIC_AXES = {
    "weekly_seq": {0: "batch_size"},
    "static_features": {0: "batch_size"},
    "position_features": {0: "batch_size"},
    "sector_id": {0: "batch_size"},
    "output": {0: "batch_size"},
}

# ONNX入力名
ONNX_INPUT_NAMES = ["weekly_seq", "static_features", "position_features", "sector_id"]
ONNX_OUTPUT_NAMES = ["output"]
