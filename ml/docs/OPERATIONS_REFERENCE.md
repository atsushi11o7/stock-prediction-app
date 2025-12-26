# 運用リファレンス

株価予測システムの運用手順。

---

## 運用フロー概要

```
初回セットアップ
  1. Universe作成 → 2. 静的特徴量付与 → 3. 過去データ取得 → 4. 初回学習
                                                                ↓
日次運用（毎営業日）                              月次運用（毎月1日）
  日次データ取得 → 推論                            静的特徴量更新 → ファインチューニング
```

---

## 初回セットアップ

### 1. 静的特徴量付与

```bash
python src/features/enrich_universe.py --config config/enrich_universe.yaml
```

yfinanceからセクター、PER、PBR、配当利回りを取得してUniverse YAMLに付与。

### 2. 過去データ取得

```bash
python src/data/fetch_daily_backfill.py --config config/fetch_daily_backfill.yaml
```

5年分の日次OHLCVデータを取得。

### 3. 初回学習

```bash
python src/training/train.py --config config/train.yaml
```

GPU推奨。約20-30分。

---

## 日次運用

毎営業日 JST 23:00頃に実行。

### パイプライン実行

```bash
python src/pipeline/daily_pipeline.py \
  --fetch-config config/fetch_daily_universe.yaml \
  --predict-config config/predict.yaml
```

### 個別実行

```bash
# データ取得のみ
python src/data/fetch_daily_universe.py --config config/fetch_daily_universe.yaml

# 推論のみ
python src/inference/predict.py --config config/predict.yaml
```

### 出力

```
predictions/
  ├── 2025-12-20.json    # 日付別
  └── latest.json        # 最新（API参照用）
```

---

## 月次運用

毎月1日 JST 00:00に実行。

### パイプライン実行

```bash
python src/pipeline/monthly_pipeline.py \
  --enrich-config config/enrich_universe.yaml \
  --finetune-config config/finetune.yaml
```

### 個別実行

```bash
# 静的特徴量更新のみ
python src/features/enrich_universe.py --config config/enrich_universe.yaml

# ファインチューニングのみ
python src/training/finetune.py --config config/finetune.yaml
```

### ファインチューニング詳細

**データサンプリング**:
- 直近1ヶ月: 約67%
- 過去データ（ランダム）: 約33%

**パラメータ**:
- エポック数: 3-5（過学習防止）
- 学習率: 0.0001（初回学習の1/10）

---

## 銘柄の追加・削除

### 銘柄追加

1. `config/universes/topix_core_30_YYYYMMDD.yaml` に銘柄を追加
2. 静的特徴量を再付与:
   ```bash
   python src/features/enrich_universe.py --config config/enrich_universe.yaml
   ```
3. 新銘柄の過去データを取得:
   ```bash
   python src/data/fetch_daily_backfill.py --config config/fetch_daily_backfill.yaml
   ```
4. 再学習（推奨）またはファインチューニング

### 銘柄削除

1. Universe YAMLから銘柄を削除
2. 静的特徴量を再付与
3. ファインチューニングで対応可能（再学習不要）

---

## トラブルシューティング

### データ取得失敗

**症状**: yfinanceからデータが取得できない

**対処**:
1. ティッカーコードを確認（Yahoo Finance形式: `2914.T`）
2. リトライ機能が自動で動作（最大3回）
3. yfinance APIのレート制限に注意

### 推論失敗（データ不足）

**症状**: `Insufficient data: only N weeks`

**対処**:
```bash
# 過去データを取得（156週分必要）
python src/data/fetch_daily_backfill.py --config config/fetch_daily_backfill.yaml
```

### ファインチューニング メモリ不足

**症状**: `RuntimeError: Out of memory`

**対処**:
- Lambdaメモリを増加: 2048MB → 3008MB
- バッチサイズを削減（config/finetune.yaml）

### S3アップロード失敗

**症状**: `AccessDenied`

**対処**:
1. IAMロールの権限確認（s3:PutObject, s3:GetObject, s3:ListBucket）
2. バケット名の確認

---

## Lambda設定

### 日次推論

| 項目 | 値 |
|------|-----|
| メモリ | 512MB |
| タイムアウト | 600秒 |
| スケジュール | `cron(0 14 ? * MON-FRI *)` (UTC 14:00 = JST 23:00) |

### 月次ファインチューニング

| 項目 | 値 |
|------|-----|
| メモリ | 2048-3008MB |
| タイムアウト | 900秒 |
| エフェメラルストレージ | 2048MB |
| スケジュール | `cron(0 15 1 * ? *)` (UTC 15:00 = JST 00:00) |

---

## モデルのロールバック

### S3から旧バージョンを取得

```bash
# 利用可能なバージョンを確認
aws s3 ls s3://stock-forecast-prod-apne1/models/onnx/

# 旧バージョンをlatest.onnxとしてコピー
aws s3 cp \
  s3://stock-forecast-prod-apne1/models/onnx/best_model_20251201.onnx \
  s3://stock-forecast-prod-apne1/models/onnx/best_model.onnx
```

---

## モニタリング

### 推奨項目

| 項目 | アラート条件 |
|-----|------------|
| 日次データ取得成功率 | エラー率 > 5% |
| 推論成功率 | エラー率 > 5% |
| Lambda実行時間 | タイムアウト発生 |
| Lambdaメモリ使用量 | 使用率 > 90% |

### ログ確認

```bash
# 日次推論
aws logs tail /aws/lambda/stock-forecast-daily-predict --follow

# ファインチューニング
aws logs tail /aws/lambda/stock-forecast-monthly-finetune --follow
```

---

## 関連ドキュメント

- [README.md](../README.md) - システム概要
- [config/README.md](../config/README.md) - 設定ファイルガイド
- [stock_prediction_model_spec.md](stock_prediction_model_spec.md) - モデル仕様
