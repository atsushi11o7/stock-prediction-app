# Xserver VPS デプロイ用 Docker 環境

このディレクトリには、Xserver VPS上でRails APIバックエンドをDockerで動かすための設定ファイルが含まれています。

## ファイル構成

```
backend/docker/
├── README.md              # このファイル
├── docker-compose.yml     # Docker Compose設定
├── Dockerfile            # Rails本番環境用Dockerfile
└── .env.example          # 環境変数のサンプル
```

---

## デプロイ手順

### 1. VPSにSSH接続

```bash
ssh -i 秘密鍵.pem root@xxx.xx.xx.xxx
```

### 2. リポジトリをクローン

```bash
cd /opt
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO/backend/docker
```

### 3. 環境変数を設定

**重要**: `.env.prod` ファイルは機密情報を含むため、Gitにコミットされません。

```bash
# .env.exampleをコピーして.env.prodを作成
cp .env.example .env.prod
nano .env.prod
```

以下の内容を実際の値に置き換える:

```bash
# PostgreSQL
POSTGRES_USER=stock_api
POSTGRES_PASSWORD=<strong_password_here>
POSTGRES_DB=stock_prediction_production

# AWS Configuration
AWS_REGION=ap-northeast-1
AWS_ACCESS_KEY_ID=<your_access_key>
AWS_SECRET_ACCESS_KEY=<your_secret_key>
S3_BUCKET_NAME=your-s3-bucket-name

# Rails
SECRET_KEY_BASE=<rails_secret_output>
```

**SECRET_KEY_BASE の生成**:
```bash
cd /opt/YOUR_REPO/backend
docker run --rm -v $(pwd):/app -w /app ruby:3.4.7 bundle exec rails secret
```

**ファイルのパーミッションを設定**:
```bash
chmod 600 .env.prod
```

### 4. Docker Composeでビルド・起動

```bash
docker-compose up -d --build
```

### 5. データベースのセットアップ

```bash
# データベース作成とマイグレーション
docker-compose exec app bundle exec rails db:create db:migrate

# 月次データのインポート（銘柄マスタ）
docker-compose exec app bundle exec rails import:monthly

# 過去データのインポート
docker-compose exec app bundle exec rails import:historical

# 最新データのインポート
docker-compose exec app bundle exec rails import:daily
```

### 6. 動作確認

```bash
# コンテナの状態確認
docker-compose ps

# ログ確認
docker-compose logs -f app

# API疎通確認
curl http://localhost:3000/api/stocks
```

---

## 日次・月次タスクの自動実行設定

### Cron設定

```bash
# crontabを編集
crontab -e

# 以下を追加
# 毎日23:00に最新データをインポート
0 23 * * * cd /opt/YOUR_REPO/backend/docker && docker-compose exec -T app bundle exec rails import:daily >> /var/log/import_daily.log 2>&1

# 毎月1日0:00に月次データを更新
0 0 1 * * cd /opt/YOUR_REPO/backend/docker && docker-compose exec -T app bundle exec rails import:monthly >> /var/log/import_monthly.log 2>&1
```

---

## 運用コマンド

### コンテナの起動・停止

```bash
# 起動
docker-compose up -d

# 停止
docker-compose down

# 再起動
docker-compose restart

# ログ確認
docker-compose logs -f app
docker-compose logs -f db
```

### データベース操作

```bash
# Railsコンソール
docker-compose exec app bundle exec rails console

# データベースに直接接続
docker-compose exec db psql -U stock_api -d stock_prediction_production

# バックアップ
docker-compose exec db pg_dump -U stock_api stock_prediction_production > backup_$(date +%Y%m%d).sql

# リストア
docker-compose exec -T db psql -U stock_api -d stock_prediction_production < backup_20250101.sql
```

### コードの更新

```bash
cd /opt/YOUR_REPO
git pull origin main

cd backend/docker
docker-compose down
docker-compose up -d --build

# マイグレーションがある場合
docker-compose exec app bundle exec rails db:migrate
```

---

## トラブルシューティング

### コンテナが起動しない

```bash
# ログを確認
docker-compose logs app

# 環境変数を確認
docker-compose config
```

### データベース接続エラー

```bash
# PostgreSQLコンテナの状態確認
docker-compose ps db

# データベース接続テスト
docker-compose exec app bundle exec rails db:migrate:status
```

### ポートが既に使用されている

```bash
# 使用中のポートを確認
sudo lsof -i :3000
sudo lsof -i :5432

# ポート番号を変更
# docker-compose.yml の ports セクションを編集
```

---

## セキュリティ

### 重要な設定

1. **`.env` ファイルのパーミッション**:
   ```bash
   chmod 600 .env
   ```

2. **Firewallの設定**:
   ```bash
   # 3000番ポートへのアクセスを制限（必要に応じて）
   sudo ufw allow from <frontend_server_ip> to any port 3000
   ```

3. **定期的なセキュリティアップデート**:
   ```bash
   # Dockerイメージの更新
   docker-compose pull
   docker-compose up -d
   ```

---

## 参考情報

- [AWS_SETUP.md](../AWS_SETUP.md) - AWS S3の設定方法
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Rails Guides - Deployment](https://guides.rubyonrails.org/getting_started.html#deploying)
