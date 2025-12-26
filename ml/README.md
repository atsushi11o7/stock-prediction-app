# 株価予測システム

TOPIX Core30銘柄を対象とした、LSTM深層学習モデルによる12ヶ月先株価予測システム

---

## 概要

| 項目 | 内容 |
|-----|------|
| データ取得 | yfinance API経由で日次データを取得 |
| 特徴量 | 週次23特徴 × 156週 + 静的6特徴 + ポジション2特徴 |
| モデル | BiLSTM + セクターEmbedding + MLP（約664K パラメータ） |
| 推論 | ONNX Runtime（CPU専用、Lambda対応） |
| 出力 | 1~12ヶ月先の月次株価予測 |

### パフォーマンス

| 項目 | 値 |
|-----|---|
| 推論時間（31銘柄） | 約2分 |
| ファインチューニング時間（CPU） | 約4分 |
| モデルサイズ（ONNX） | 約2.5MB |

---

## アーキテクチャ

```
┌─────────────────────────────────────────────────────────────────┐
│                        AWS Lambda                                │
├─────────────────────────────────────────────────────────────────┤
│  stock-forecast-daily          stock-forecast-monthly           │
│  ┌─────────────────────┐       ┌─────────────────────┐          │
│  │ ECR Container Image │       │ ECR Container Image │          │
│  │ - ONNX Runtime      │       │ - PyTorch CPU       │          │
│  │ - 推論専用 (~300MB) │       │ - 学習可能 (~700MB) │          │
│  └──────────┬──────────┘       └──────────┬──────────┘          │
│             │                              │                     │
│  EventBridge: 平日23:00 JST    EventBridge: 毎月1日 9:00 JST    │
└─────────────┼──────────────────────────────┼─────────────────────┘
              │                              │
              ▼                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     S3: stock-forecast-prod-apne1               │
├─────────────────────────────────────────────────────────────────┤
│  daily/           # 日次OHLCVデータ                              │
│  predictions/     # 推論結果                                     │
│  models/onnx/     # ONNXモデル                                   │
│  checkpoints/     # PyTorchチェックポイント                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## ローカル実行

### 初回セットアップ

```bash
# 1. 静的特徴量の付与
python src/features/enrich_universe.py --config config/enrich_universe.yaml

# 2. 過去データ取得（5年分）
python src/data/fetch_daily_backfill.py --config config/fetch_daily_backfill.yaml

# 3. 初回学習（GPU推奨）
python src/training/train.py --config config/train.yaml
```

### 日次パイプライン

```bash
python src/pipeline/daily_pipeline.py \
  --fetch-config config/fetch_daily_universe.yaml \
  --predict-config config/predict.yaml
```

### 月次パイプライン

```bash
python src/pipeline/monthly_pipeline.py \
  --enrich-config config/enrich_universe.yaml \
  --finetune-config config/finetune.yaml
```

---

## AWS Lambda デプロイ

### Lambda設定

| 項目 | Daily | Monthly |
|------|-------|---------|
| 関数名 | `stock-forecast-daily` | `stock-forecast-monthly` |
| メモリ | 1024 MB | 3008 MB |
| タイムアウト | 10分 | 15分 |
| スケジュール | `cron(0 14 ? * MON-FRI *)` | `cron(0 0 1 * ? *)` |
| 実行時刻 (JST) | 平日 23:00 | 毎月1日 9:00 |

### Dockerビルド・プッシュ

```bash
cd ml

# Daily
docker build --provenance=false -t stock-forecast-daily:latest -f docker/daily/Dockerfile .
docker tag stock-forecast-daily:latest <ACCOUNT_ID>.dkr.ecr.ap-northeast-1.amazonaws.com/stock-forecast-daily:latest
docker push <ACCOUNT_ID>.dkr.ecr.ap-northeast-1.amazonaws.com/stock-forecast-daily:latest

# Monthly
docker build --provenance=false -t stock-forecast-monthly:latest -f docker/monthly/Dockerfile .
docker tag stock-forecast-monthly:latest <ACCOUNT_ID>.dkr.ecr.ap-northeast-1.amazonaws.com/stock-forecast-monthly:latest
docker push <ACCOUNT_ID>.dkr.ecr.ap-northeast-1.amazonaws.com/stock-forecast-monthly:latest
```

### IAM権限

Lambda実行ロールに以下のS3権限を付与:

```json
{
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Action": ["s3:GetObject", "s3:PutObject", "s3:ListBucket"],
        "Resource": [
            "arn:aws:s3:::stock-forecast-prod-apne1",
            "arn:aws:s3:::stock-forecast-prod-apne1/*"
        ]
    }]
}
```

### 料金

無料枠（40万GB-秒/月）内で収まるため、**実質無料**で運用可能

---

## ディレクトリ構成

```
ml/
├── config/                    # 設定ファイル
│   ├── train.yaml             # 学習設定
│   ├── predict.yaml           # 推論設定
│   ├── finetune.yaml          # ファインチューニング設定
│   └── universes/             # Universe定義
├── src/
│   ├── common/                # 共通モジュール
│   ├── data/                  # データ取得
│   ├── features/              # 特徴量計算
│   ├── inference/             # ONNX推論
│   ├── model_src/             # モデル定義
│   ├── pipeline/              # パイプライン
│   └── training/              # 学習・ファインチューニング
├── docker/
│   ├── daily/                 # 日次Lambda用Dockerfile
│   └── monthly/               # 月次Lambda用Dockerfile
└── docs/                      # 詳細ドキュメント
```

---

## 出力形式

### 予測結果 (predictions/latest.json)

```json
{
  "timestamp": "2025-12-20T23:00:00",
  "predictions": [
    {
      "ticker": "2914.T",
      "current_price": 4250.5,
      "predicted_12m_price": 4625.3,
      "predicted_12m_return": 0.088,
      "predictions": [
        {"month": 1, "predicted_price": 4280.2, "return": 0.007},
        {"month": 12, "predicted_price": 4625.3, "return": 0.088}
      ]
    }
  ]
}
```

---

## トラブルシューティング

| 症状 | 対処 |
|------|------|
| S3 Access Denied | Lambda実行ロールにS3権限を追加 |
| データ不足エラー | `fetch_daily_backfill.py` で過去データを取得 |
| ONNXモデルが見つからない | `train.py` で初回学習を実行 |
| Lambda タイムアウト | メモリを増やす / エポック数を減らす |

---

## 関連ドキュメント

| ドキュメント | 内容 |
|------------|------|
| [config/README.md](config/README.md) | 設定ファイルの詳細 |
| [docs/stock_prediction_model_spec.md](docs/stock_prediction_model_spec.md) | モデル仕様書 |
| [docs/OPERATIONS_REFERENCE.md](docs/OPERATIONS_REFERENCE.md) | 運用リファレンス |
