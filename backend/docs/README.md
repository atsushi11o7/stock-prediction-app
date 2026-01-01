# Rails API バックエンド

株価予測アプリケーションのRails 7.2 API実装

---

## システム構成

```
AWS Lambda (ML)
  ├── 日次株価データ取得・予測実行 (23:00 JST)
  └── S3にデータ保存
       ↓
S3: stock-forecast-prod-apne1
  ├── daily/*.json (株価データ)
  ├── predictions/*.json (予測データ)
  └── config/universes/*.yaml (銘柄マスタ)
       ↓
PostgreSQL Database
  ├── companies, stock_prices, kpi_snapshots
  └── forecast_runs, forecast_details
       ↓
Rails API (17エンドポイント)
       ↓
Next.js Frontend
```

---

## 実装状況

### ✅ 完了済み

**データベース層**
- スキーマ設計（7テーブル）
- マイグレーションファイル
- モデル実装（関連・バリデーション）
- YARD形式ドキュメント

**API層**
- 17エンドポイント実装
- コントローラー（5個）
- シリアライザー
- サービスオブジェクト
- CORS設定

**データインポート**
- S3クライアントヘルパー
- 月次インポート（銘柄マスタ・KPI）
- 日次インポート（株価・予測）
- 過去データ一括インポート

**環境構築**
- 開発環境（Dev Container）
- 本番環境（Docker Compose）
- 環境変数管理
- セキュリティ設定

---

## データベース

### テーブル構成

| テーブル | レコード数 | 用途 |
|---------|----------|------|
| sectors | 11 | セクター分類 |
| industries | 28 | 業種分類 |
| companies | 31 | 企業マスタ |
| stock_prices | 73,405 | 株価データ (2015-2025) |
| kpi_snapshots | 31 | KPI月次スナップショット |
| forecast_runs | 2 | 予測実行履歴 |
| forecast_details | 60 | 予測詳細 |

詳細: [DATABASE.md](./DATABASE.md)

---

## API エンドポイント

### 銘柄関連
- `GET /api/stocks` - 銘柄一覧
- `GET /api/stocks/:ticker` - 銘柄詳細
- `GET /api/stocks/:ticker/prices` - 株価データ
- `GET /api/stocks/:ticker/kpis` - KPIデータ
- `GET /api/stocks/:ticker/forecast` - 予測チャートデータ

### マーケット関連
- `GET /api/market/overview` - マーケット概要
- `GET /api/market/sectors` - セクター別パフォーマンス
- `GET /api/market/movers` - 騰落率ランキング

### 予測関連
- `GET /api/forecasts/latest` - 最新予測一覧
- `GET /api/forecasts/top_returns` - 予測リターン上位
- `GET /api/forecasts/statistics` - 予測統計

### スクリーニング
- `GET /api/screening/high_dividend` - 高配当銘柄
- `GET /api/screening/low_per` - 低PER銘柄
- `GET /api/screening/value_stocks` - バリュー株
- `GET /api/screening/growth_stocks` - 成長株

詳細: [API.md](./API.md)

---

## データインポート

### 初回セットアップ
```bash
rails import:monthly      # 銘柄マスタ・KPI
rails import:historical   # 過去データ一括
```

### 日常運用
```bash
rails import:daily        # 日次更新（毎営業日23:00）
rails import:monthly      # 月次更新（月初）
```

詳細: [SETUP.md](./SETUP.md)

---

## デプロイ環境

### 開発環境
- VS Code Dev Container
- PostgreSQL 16
- Rails 7.2 (development mode)
- 環境変数: `/workspace/.devcontainer/backend/.env`

### 本番環境（Xserver VPS）
- Docker Compose
- PostgreSQL 16
- Rails 7.2 (production mode)
- 環境変数: `/workspace/backend/docker/.env.prod`

---

## ディレクトリ構成

```
backend/
├── app/
│   ├── controllers/api/      # APIコントローラー
│   ├── models/               # Activeモデル
│   ├── serializers/          # JSONシリアライザー
│   └── services/             # サービスオブジェクト
├── config/
│   ├── routes.rb             # ルーティング
│   └── initializers/         # 初期化設定
├── db/
│   ├── migrate/              # マイグレーション
│   └── schema.rb             # スキーマ定義
├── lib/
│   ├── tasks/                # Rakeタスク
│   └── s3_client_helper.rb   # S3ヘルパー
├── docker/                   # 本番環境用
│   ├── docker-compose.yml
│   ├── Dockerfile
│   ├── .env.example
│   └── README.md
└── docs/                     # ドキュメント
    ├── README.md             # このファイル
    ├── API.md
    ├── DATABASE.md
    └── SETUP.md
```

---

## 次のステップ

### デプロイ準備
1. GitHubにプッシュ
2. Xserver VPSにリポジトリクローン
3. `.env.prod` ファイル作成・設定
4. Docker Compose起動
5. 初回データインポート

### フロントエンド連携
1. CORS設定の確認
2. API疎通テスト
3. 環境変数設定（`FRONTEND_URL`）

---

## 主要コマンド

### 開発環境
```bash
# サーバー起動
rails server

# マイグレーション
rails db:migrate

# コンソール
rails console

# テスト
rails test
```

### 本番環境（Docker）
```bash
# ビルド・起動
cd docker
docker-compose up -d --build

# ログ確認
docker-compose logs -f app

# データベース操作
docker-compose exec app rails db:migrate
docker-compose exec app rails console

# データインポート
docker-compose exec app rails import:monthly
docker-compose exec app rails import:daily
```

---

## トラブルシューティング

### データベース接続エラー
```bash
docker-compose ps db
docker-compose exec app rails db:migrate:status
```

### S3接続エラー
```bash
# 環境変数確認
docker-compose exec app printenv | grep AWS
```

### ポート競合
```bash
sudo lsof -i :3000
sudo lsof -i :5432
```

---

## ドキュメント

- [API.md](./API.md) - API仕様とデータ取得ガイド
- [DATABASE.md](./DATABASE.md) - データベース設計とテーブル構造
- [SETUP.md](./SETUP.md) - AWS設定とデータインポート手順
- [docker/README.md](../docker/README.md) - デプロイ手順
