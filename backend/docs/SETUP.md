# セットアップガイド

AWS S3設定とデータインポート手順

---

## 1. AWS S3設定

### IAMアクセスキー作成

1. [AWS Console](https://console.aws.amazon.com/) → IAM
2. ユーザー選択 → Security credentials
3. Create access key → CLI を選択
4. Access key ID と Secret access key をコピー

### 必要なIAM権限

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::stock-prediction-data",
        "arn:aws:s3:::stock-prediction-data/*"
      ]
    }
  ]
}
```

### S3データ構造

```
s3://stock-prediction-data/
├── config/universes/
│   └── enrich_topix_core_30_20251031.yaml  # 銘柄マスタ（月次更新）
├── daily/
│   ├── 2025-12-24.json
│   ├── 2025-12-25.json
│   └── latest.json  # 最新データ
└── predictions/
    ├── 2025-12-24.json
    ├── 2025-12-25.json
    └── latest.json  # 最新データ
```

---

## 2. 環境変数設定

### 開発環境

`/workspace/backend/.env.example` を参照:

```bash
AWS_REGION=ap-northeast-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
S3_BUCKET_NAME=stock-prediction-data
```

`.env` ファイルを作成してGitにコミットしない（`.gitignore`に追加済み）

### 本番環境（Xserver VPS）

`/workspace/backend/docker/.env.prod` を作成:

```bash
# PostgreSQL
POSTGRES_USER=stock_api
POSTGRES_PASSWORD=strong_password_here
POSTGRES_DB=stock_prediction_production

# AWS Configuration
AWS_REGION=ap-northeast-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
S3_BUCKET_NAME=stock-prediction-data

# Rails
SECRET_KEY_BASE=generated_by_rails_secret
```

**パーミッション設定**:
```bash
chmod 600 .env.prod
```

---

## 3. データインポート

### 初回セットアップ

```bash
# 1. 環境変数設定
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."

# 2. データベース準備
rails db:create
rails db:migrate

# 3. データインポート
rails import:monthly      # 銘柄マスタ・KPI
rails import:historical   # 過去データ一括

# 4. サーバー起動
rails server
```

### 日常運用

```bash
# 毎営業日23:00以降
rails import:daily

# 月1回
rails import:monthly
```

### 特定日のデータインポート

```bash
rails import:daily_for_date[2025-12-20]
```

---

## 4. Rakeタスク詳細

### rails import:monthly

**処理内容**:
- `config/universes/*.yaml` から企業情報取得
- セクター・業種の登録・更新
- 企業情報の登録・更新
- KPIスナップショット作成

**実行例**:
```
=== Starting monthly static data import ===
✓ Loaded 31 companies from YAML

Companies: 31 total, 0 new, 5 updated
Sectors: 11 (+0 new)
Industries: 28 (+0 new)
KPI Snapshots: 31 created
```

---

### rails import:daily

**処理内容**:
- `daily/latest.json` から最新株価データ取得
- `predictions/latest.json` から最新予測データ取得
- 重複チェック（自動スキップ）

**実行例**:
```
=== Starting daily data import ===

[1/2] Importing daily stock prices...
✓ Stock prices imported: 31

[2/2] Importing predictions...
Created forecast run #251
✓ Forecasts imported: 30

Total: Companies: 31, Stock Prices: 7781
```

---

### rails import:historical

**処理内容**:
- `daily/` 配下の全JSONファイルをインポート
- `predictions/` 配下の全JSONファイルをインポート
- `latest.json` は除外

**実行例**:
```
=== Starting historical data import ===

Found 250 daily files
[1/250] Processing 2024-01-04... ✓ Imported 31 prices
...
✓ Stock prices: 7750 records
✓ Predictions: 250 runs, 7500 forecasts
```

---

## 5. 定期実行設定

### Cron設定

VPSにSSH接続後、`crontab -e`:

```cron
# 毎営業日23:30に日次データ取得
30 23 * * * cd /opt/YOUR_REPO/backend/docker && docker-compose exec -T app bundle exec rails import:daily >> /var/log/import_daily.log 2>&1

# 毎月1日0:00に月次データ更新
0 0 1 * * cd /opt/YOUR_REPO/backend/docker && docker-compose exec -T app bundle exec rails import:monthly >> /var/log/import_monthly.log 2>&1
```

### systemd timer設定

`/etc/systemd/system/stock-import-daily.service`:
```ini
[Unit]
Description=Stock Price Import - Daily

[Service]
Type=oneshot
User=rails
WorkingDirectory=/workspace/backend
Environment="RAILS_ENV=production"
EnvironmentFile=/workspace/backend/.env
ExecStart=/usr/local/bin/rails import:daily
```

`/etc/systemd/system/stock-import-daily.timer`:
```ini
[Unit]
Description=Stock Price Import - Daily Timer

[Timer]
OnCalendar=Mon-Fri 23:30:00
Persistent=true

[Install]
WantedBy=timers.target
```

有効化:
```bash
sudo systemctl enable stock-import-daily.timer
sudo systemctl start stock-import-daily.timer
```

---

## 6. トラブルシューティング

### AWS認証失敗

```
ERROR: The AWS Access Key Id you provided does not exist
```

**解決方法**:
```bash
# 環境変数確認
echo $AWS_ACCESS_KEY_ID
echo $AWS_SECRET_ACCESS_KEY

# IAMで有効化確認
```

---

### S3ファイルが見つからない

```
ERROR: File not found: s3://bucket/daily/latest.json
```

**解決方法**:
```bash
# S3確認
aws s3 ls s3://stock-prediction-data/daily/

# MLパイプライン実行確認
```

---

### 企業が見つからない

```
⚠ Skipping 7203.T - company not found
```

**解決方法**:
```bash
# 先に月次データをインポート
rails import:monthly

# その後、日次データを再実行
rails import:daily
```

---

### 重複データのスキップ（正常動作）

```
✓ Stock prices imported: 0
  Skipped (duplicates): 31
```

既にインポート済みのデータは自動的にスキップされます。

---

## 7. データ欠損の確認と修復

### 欠損日を特定

```bash
rails console
```

```ruby
# 最新データ日付
StockPrice.maximum(:date)

# 期間別データ件数
StockPrice.where(date: '2025-12-20'..'2025-12-26').group(:date).count
# => {"2025-12-20"=>31, "2025-12-21"=>0, "2025-12-26"=>31}
```

### 欠損データの取り込み

```bash
rails import:daily_for_date[2025-12-21]
```

---

## よくある質問

**Q: 日次タスクを複数回実行するとどうなりますか？**
A: 重複データは自動スキップされるため問題ありません。

**Q: 月次タスクを実行し忘れた場合は？**
A: いつでも実行可能です。最新のYAMLから情報を取得します。

**Q: DBをリセットして再インポートしたい場合は？**
A:
```bash
rails db:drop
rails db:create
rails db:migrate
rails import:monthly
rails import:historical
```
