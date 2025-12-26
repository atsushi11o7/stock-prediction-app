# 設定ファイルガイド

すべてのスクリプトは設定ファイル（YAML）で動作を制御します。

---

## 設定ファイル一覧

| ファイル | 用途 | 主な設定 |
|---------|------|---------|
| `train.yaml` | 初回学習 | モデル構造、学習パラメータ、出力先 |
| `predict.yaml` | 推論 | モデルパス、入出力ディレクトリ |
| `finetune.yaml` | ファインチューニング | エポック数、学習率、チェックポイント |
| `enrich_universe.yaml` | 静的特徴量付与 | 入出力YAMLパス、更新モード |
| `fetch_daily_universe.yaml` | 日次データ取得 | Universe、出力先 |
| `fetch_daily_backfill.yaml` | バックフィル | 期間、Universe、出力先 |
| `sectors.yaml` | セクター定義 | セクター名とID（共通） |

---

## 環境切り替え（`env`フラグ）

すべての設定ファイルは `env` フラグで環境を切り替えられます:

```yaml
# config/train.yaml
env: "local"  # "local" または "s3"

local:
  input:
    daily_data_dir: "data/training/daily"
  output:
    checkpoint_dir: "checkpoints"
    onnx_dir: "models/onnx"

s3:
  bucket: "stock-forecast-prod-apne1"
  input:
    daily_data_prefix: "market_data/training/daily"
  output:
    checkpoint_prefix: "models/checkpoints"
    onnx_prefix: "models/onnx"
```

ローカル開発時は `env: "local"`、本番（AWS Lambda）では `env: "s3"` に切り替えるだけで動作します。

---

## Universe YAMLの指定

各環境セクション内の`input`で指定します:

```yaml
# ローカル環境
local:
  input:
    universe_path: "config/universes/enrich_topix_core_30_20251031.yaml"

# S3環境
s3:
  bucket: "stock-forecast-prod-apne1"
  input:
    universe_key: "config/universes/enrich_topix_core_30_20251031.yaml"
```

環境（`env`）に応じて適切なパスが自動的に使用されます。

---

## 各設定ファイルの詳細

### train.yaml（初回学習）

```yaml
env: "local"  # "local" または "s3"

seed: 42
deterministic: true

data:
  batch_size: 32
  num_workers: 4
  train_ratio: 0.7
  val_ratio: 0.15
  test_ratio: 0.15

model:
  model_type: "lstm"
  lstm_hidden_size: 128
  lstm_num_layers: 2
  lstm_dropout: 0.2
  use_bidirectional: true
  mlp_hidden_sizes: [256, 128, 64]
  mlp_dropout: 0.3

optimizer:
  learning_rate: 0.001
  weight_decay: 0.00001

training:
  max_epochs: 100
  accelerator: "auto"
  early_stopping_patience: 15

onnx:
  export: true
  opset_version: 14

local:
  input:
    daily_data_dir: "data/training/daily"
    universe_path: "config/universes/enrich_topix_core_30_20251031.yaml"
  output:
    checkpoint_dir: "checkpoints"
    onnx_dir: "models/onnx"
    logs_dir: "logs"

s3:
  bucket: "stock-forecast-prod-apne1"
  input:
    daily_data_prefix: "market_data/training/daily"
    universe_key: "config/universes/enrich_topix_core_30_20251031.yaml"
  output:
    checkpoint_prefix: "models/checkpoints"
    onnx_prefix: "models/onnx"
```

#### 出力ファイル

```
checkpoints/
  └── best_model.ckpt           # ベストモデル（固定名、上書き更新）

models/onnx/
  ├── best_model.onnx           # ONNXモデル（固定名）
  └── best_model.json           # メタデータ（セクターマッピング等）
```

---

### predict.yaml（推論）

```yaml
env: "local"

model:
  onnx_path: "models/onnx/best_model.onnx"

local:
  input:
    daily_data_dir: "data/training/daily"
    universe_path: "config/universes/enrich_topix_core_30_20251031.yaml"
  output:
    dir: "predictions"

s3:
  bucket: "stock-forecast-prod-apne1"
  input:
    daily_data_prefix: "daily"
    universe_key: "config/universes/enrich_topix_core_30_20251031.yaml"
  output:
    predictions_prefix: "predictions"
```

#### 出力ファイル

```
predictions/
  ├── 2025-12-20.json    # 日付別ファイル（履歴用）
  ├── 2025-12-19.json
  ├── ...
  └── latest.json        # 最新の予測結果（バックエンドAPI参照用）
```

---

### finetune.yaml（ファインチューニング）

```yaml
env: "local"

finetuning:
  recent_months: 1
  num_epochs: 5
  learning_rate: 0.0001
  batch_size: 32

local:
  input:
    checkpoint_path: "checkpoints/best_model.ckpt"
    daily_data_dir: "data/training/daily"
    universe_path: "config/universes/enrich_topix_core_30_20251031.yaml"
  output:
    onnx_dir: "models/onnx"
    checkpoint_dir: "checkpoints"

s3:
  bucket: "stock-forecast-prod-apne1"
  input:
    checkpoint_key: "models/checkpoints/best_model.ckpt"
    daily_data_prefix: "daily"
    universe_key: "config/universes/enrich_topix_core_30_20251031.yaml"
  output:
    onnx_prefix: "models/onnx"
```

#### 推奨パラメータ

| パラメータ | 推奨値 | 説明 |
|-----------|-------|------|
| `recent_months` | 1 | 直近1ヶ月のデータを使用 |
| `num_epochs` | 3-5 | 少なめ（過学習防止） |
| `learning_rate` | 0.0001 | 元の学習率の1/10 |
| `batch_size` | 32 | メモリに応じて調整 |

---

### fetch_daily_universe.yaml（日次データ取得）

```yaml
env: "local"

local:
  input:
    universe_path: "config/universes/enrich_topix_core_30_20251031.yaml"
  output:
    dir: "data/serving/daily"

s3:
  bucket: "stock-forecast-prod-apne1"
  input:
    universe_key: "config/universes/enrich_topix_core_30_20251031.yaml"
  output:
    daily_prefix: "market_data/serving/daily"
```

---

### enrich_universe.yaml（静的特徴量付与）

```yaml
input_path: "config/universes/topix_core_30_20251031.yaml"
output_path: "config/universes/enrich_topix_core_30_20251031.yaml"
update_mode: "valuation-only"  # "full" または "valuation-only"
```

---

## Universeディレクトリ構成

```
config/universes/
  ├── topix_core_30_20251031.yaml         # 基本Universe（ティッカーリスト）
  └── enrich_topix_core_30_20251031.yaml  # 静的特徴量付きUniverse
```

### Universe YAMLの形式

```yaml
# config/universes/enrich_topix_core_30_20251031.yaml
name: "TOPIX Core 30"
as_of: "2025-10-31"

universe:
  - ticker: "2914.T"
    name: "Japan Tobacco Inc."
    sector: "Consumer Defensive"
    per: 15.2
    pbr: 2.1
    dividend_yield: 4.5
    market_cap: 5000000000000
    avg_volume_90d: 5000000
    volatility_90d: 0.25
  - ticker: "3382.T"
    name: "Seven & I Holdings Co., Ltd."
    sector: "Consumer Defensive"
    # ...
```

---

## S3パス構成（本番環境）

```
s3://stock-forecast-prod-apne1/
  ├── market_data/
  │   ├── training/daily/          # 学習用日次データ
  │   │   ├── 2025-12-19.json
  │   │   ├── 2025-12-20.json
  │   │   └── latest.json
  │   └── serving/daily/           # 推論用日次データ
  │       ├── 2025-12-20.json
  │       └── latest.json
  ├── models/
  │   ├── checkpoints/
  │   │   └── best_model.ckpt      # 学習済みチェックポイント
  │   └── onnx/
  │       ├── best_model.onnx      # ONNXモデル
  │       └── best_model.json      # メタデータ
  └── predictions/
      ├── 2025-12-20.json          # 日付別予測結果
      └── latest.json              # 最新予測結果
```
