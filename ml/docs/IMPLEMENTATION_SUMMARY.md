# 株価予測システム 実装サマリ

TOPIX Core30銘柄を対象とした株価予測システムの実装概要。

## システム構成

### 主要コンポーネント

| コンポーネント | 用途 | 実行環境 |
|--------------|------|---------|
| データパイプライン | 日次データ取得、静的特徴量付与 | ローカル / Lambda |
| 学習パイプライン | LSTM モデル学習、ONNX エクスポート | ローカル（GPU推奨） |
| 推論パイプライン | 12ヶ月先株価予測 | Lambda（ONNX Runtime） |
| ファインチューニング | 月次モデル更新 | Lambda（CPU） |

---

## ディレクトリ構成

```
ml/
├── config/                    # 設定ファイル
│   ├── train.yaml
│   ├── predict.yaml
│   ├── finetune.yaml
│   └── universes/             # Universe定義
├── src/
│   ├── common/                # 共通モジュール
│   │   ├── constants.py       # 定数定義
│   │   ├── logging_config.py
│   │   └── s3_operations.py
│   ├── data/
│   │   ├── utils/
│   │   │   ├── config.py      # 設定読み込み（env切り替え対応）
│   │   │   ├── io.py          # データI/O（local/S3統一インターフェース）
│   │   │   └── universe_loader.py
│   │   ├── fetch_daily_universe.py
│   │   └── fetch_daily_backfill.py
│   ├── features/
│   │   ├── enrich_universe.py
│   │   ├── weekly_features.py
│   │   ├── valuation_features.py
│   │   └── position_features.py
│   ├── inference/
│   │   └── predict.py
│   ├── model_src/
│   │   ├── models/lstm_model.py
│   │   ├── lit_modules/lit_model.py
│   │   └── datamodules/lstm_datamodule.py
│   ├── pipeline/
│   │   ├── daily_pipeline.py
│   │   └── monthly_pipeline.py
│   └── training/
│       ├── train.py
│       └── finetune.py
├── data/training/daily/       # 学習用日次データ
├── checkpoints/               # 学習チェックポイント
├── models/onnx/               # ONNXモデル
└── predictions/               # 予測結果
```

---

## 主要機能

### 1. データパイプライン

**静的特徴量付与** (`enrich_universe.py`)
- yfinanceからセクター、PER、PBR、配当利回りを取得
- Universe YAMLに静的情報を付与

**日次データ取得** (`fetch_daily_universe.py`, `fetch_daily_backfill.py`)
- yfinance APIから日次OHLCVを取得
- JSON形式で日付別ファイルとして保存

**統一データI/O** (`io.py`)
- `load_daily_data()`: ローカル/S3両対応の統一インターフェース
- `lookback_days`パラメータで必要期間のみ効率的に読み込み

### 2. 特徴量計算

**週次時系列特徴量** (`weekly_features.py`) - 23特徴量 × 156週
- OHLCV (5): 週内高値安値、出来高等
- リターン (5): 週次、4週、13週、26週、52週
- 移動平均 (3): 4週、13週、26週MA
- トレンド位置 (3): MAからの乖離率
- 高値安値位置 (2): 52週高値/安値からの位置
- ボラティリティ (2): 13週、26週
- 出来高比率 (1)
- ローソク足形状 (2)

**静的特徴量** (`valuation_features.py`) - 6特徴量
- 長期統計 (3): 平均リターン、ボラティリティ、最大DD
- バリュエーション (3): PER、PBR、配当利回り

**位置特徴量** (`position_features.py`) - 2特徴量
- 年間サイクル性: sin/cos(週番号/52)

### 3. モデル

**アーキテクチャ** (`lstm_model.py`)
```
入力:
  - weekly_seq: (batch, 156, 23)
  - static_features: (batch, 6)
  - position_features: (batch, 2)
  - sector_id: (batch,)

処理:
  BiLSTM → SectorEmbedding → Concat → MLP

出力:
  - 1〜12ヶ月の対数リターン (batch, 12)
```

**モデルサイズ**: 約664Kパラメータ、約2.5MB (ONNX)

### 4. 学習・推論

**初回学習** (`train.py`)
- PyTorch Lightning使用
- Early Stopping、チェックポイント保存
- ONNXエクスポート

**推論** (`predict.py`)
- ONNX Runtime使用（CPU専用）
- 各銘柄の12ヶ月先株価を予測

**ファインチューニング** (`finetune.py`)
- 直近1ヶ月(67%) + 過去データランダム(33%)
- 少数エポック（3-5）で過学習防止
- CPU専用（Lambda対応）

---

## 設定ファイルアーキテクチャ

すべてのスクリプトは設定ファイル（YAML）で動作を制御。

**環境切り替え** (`env`フラグ)
```yaml
env: "local"  # または "s3"

local:
  input:
    daily_data_dir: "data/training/daily"
  output:
    checkpoint_dir: "checkpoints"

s3:
  bucket: "stock-forecast-prod-apne1"
  input:
    daily_data_prefix: "daily"
  output:
    checkpoint_prefix: "models/checkpoints"
```

**Universe指定** (`defaults`)
```yaml
defaults:
  - universes: enrich_topix_core_30_20251031
```

詳細は [config/README.md](../config/README.md) を参照。

---

## パフォーマンス

| 処理 | 時間 | メモリ |
|------|------|--------|
| 初回学習（GPU） | 20-30分 | 4-8GB |
| ファインチューニング（CPU） | 5-7分 | 1.5-2GB |
| 推論（31銘柄） | 3-5秒 | 200-300MB |

---

## AWS Lambda設定

### 日次推論
- メモリ: 512MB
- タイムアウト: 600秒
- スケジュール: 毎営業日 JST 23:00

### 月次ファインチューニング
- メモリ: 2048-3008MB
- タイムアウト: 900秒
- スケジュール: 毎月1日 JST 00:00

---

## 主要な設計決定

1. **設定ファイルベースアーキテクチャ**: `env`フラグでローカル/S3を切り替え
2. **ONNXエクスポート**: Lambda でのCPU推論に対応
3. **統一データI/O**: `io.py`でローカル/S3の抽象化
4. **時系列分割**: データリークを防ぐ70%/15%/15%分割
5. **効率的データ読み込み**: `lookback_days`で必要期間のみ読み込み
