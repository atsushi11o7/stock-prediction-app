# データベース設計

PostgreSQL データベーススキーマとテーブル構造

---

## ER図

```
sectors (1) ────< (N) industries
   │
   └───< (N) companies ──┬──< (N) stock_prices
                         │
                         ├──< (N) kpi_snapshots
                         │
                         └──< (N) forecast_details >─── forecast_runs (1)
```

---

## テーブル一覧

| テーブル | レコード数 | 用途 |
|---------|----------|------|
| sectors | 11 | セクター分類 |
| industries | 28 | 業種分類 |
| companies | 31 | 企業マスタ |
| stock_prices | 73,405 | 株価データ (2015-2025) |
| kpi_snapshots | 31 | KPI月次スナップショット |
| forecast_runs | 2 | 予測実行履歴 |
| forecast_details | 60 | 予測詳細データ |

---

## 1. sectors（セクターマスタ）

| カラム | 型 | NULL | 制約 | 説明 |
|-------|-----|------|------|------|
| id | bigint | NOT NULL | PK | 主キー |
| name | varchar(255) | NOT NULL | UNIQUE | セクター名 |
| created_at | timestamp | NOT NULL | - | 作成日時 |
| updated_at | timestamp | NOT NULL | - | 更新日時 |

**データ例**: Consumer Defensive, Technology, Financial Services

---

## 2. industries（業種マスタ）

| カラム | 型 | NULL | 制約 | 説明 |
|-------|-----|------|------|------|
| id | bigint | NOT NULL | PK | 主キー |
| name | varchar(255) | NOT NULL | - | 業種名 |
| sector_id | bigint | NOT NULL | FK → sectors | セクターID |
| created_at | timestamp | NOT NULL | - | 作成日時 |
| updated_at | timestamp | NOT NULL | - | 更新日時 |

**インデックス**: UNIQUE (sector_id, name)

**データ例**: Tobacco, Chemicals, Auto Manufacturers

---

## 3. companies（銘柄マスタ）

| カラム | 型 | NULL | 制約 | 説明 |
|-------|-----|------|------|------|
| id | bigint | NOT NULL | PK | 主キー |
| code | varchar(10) | NOT NULL | - | 証券コード |
| ticker | varchar(20) | NOT NULL | UNIQUE | ティッカー |
| name | varchar(255) | NOT NULL | - | 企業名 |
| sector_id | bigint | NULL | FK → sectors | セクターID |
| industry_id | bigint | NULL | FK → industries | 業種ID |
| created_at | timestamp | NOT NULL | - | 作成日時 |
| updated_at | timestamp | NOT NULL | - | 更新日時 |

**インデックス**:
- UNIQUE (ticker)
- INDEX (code)

**データ例**:
- ticker: "2914.T", name: "日本たばこ産業"
- ticker: "7203.T", name: "トヨタ自動車"

---

## 4. stock_prices（株価データ）

| カラム | 型 | NULL | 制約 | 説明 |
|-------|-----|------|------|------|
| id | bigint | NOT NULL | PK | 主キー |
| company_id | bigint | NOT NULL | FK → companies | 銘柄ID |
| date | date | NOT NULL | - | 日付 |
| open | decimal(10,2) | NULL | - | 始値 |
| high | decimal(10,2) | NULL | - | 高値 |
| low | decimal(10,2) | NULL | - | 安値 |
| close | decimal(10,2) | NOT NULL | - | 終値 |
| adj_close | decimal(10,2) | NULL | - | 調整後終値 |
| volume | bigint | NULL | - | 出来高 |
| change_pct | decimal(8,4) | NULL | - | 前日比率（%） |
| created_at | timestamp | NOT NULL | - | 作成日時 |
| updated_at | timestamp | NOT NULL | - | 更新日時 |

**インデックス**:
- UNIQUE (company_id, date)
- INDEX (date)

**データソース**: S3 `daily/*.json` (日次更新)

---

## 5. kpi_snapshots（KPI月次スナップショット）

| カラム | 型 | NULL | 説明 |
|-------|-----|------|------|
| id | bigint | NOT NULL | 主キー |
| company_id | bigint | NOT NULL | 銘柄ID（FK → companies） |
| date | date | NOT NULL | スナップショット日付 |
| per | decimal(10,4) | NULL | 株価収益率 |
| pbr | decimal(10,4) | NULL | 株価純資産倍率 |
| dividend_yield | decimal(8,4) | NULL | 配当利回り（%） |
| market_cap | decimal(15,2) | NULL | 時価総額（億円） |
| eps | decimal(10,2) | NULL | 1株あたり利益 |
| bps | decimal(10,2) | NULL | 1株あたり純資産 |
| roe | decimal(8,4) | NULL | 自己資本利益率（%） |
| roa | decimal(8,4) | NULL | 総資産利益率（%） |
| psr | decimal(10,4) | NULL | 株価売上高倍率 |
| equity_ratio | decimal(8,4) | NULL | 自己資本比率（%） |
| operating_margin | decimal(8,4) | NULL | 営業利益率（%） |
| net_margin | decimal(8,4) | NULL | 純利益率（%） |
| payout_ratio | decimal(8,4) | NULL | 配当性向（%） |
| revenue_growth | decimal(8,4) | NULL | 売上高成長率（%） |
| earnings_growth | decimal(8,4) | NULL | 利益成長率（%） |
| created_at | timestamp | NOT NULL | 作成日時 |
| updated_at | timestamp | NOT NULL | 更新日時 |

**インデックス**:
- UNIQUE (company_id, date)
- INDEX (market_cap, roe, dividend_yield)

**データソース**: S3 `config/universes/*.yaml` (月次更新)

**現在の利用カラム**: per, pbr, dividend_yield のみ（将来拡張予定）

---

## 6. forecast_runs（予測実行履歴）

| カラム | 型 | NULL | 説明 |
|-------|-----|------|------|
| id | bigint | NOT NULL | 主キー |
| predicted_at | timestamp | NOT NULL | 予測実行日時 |
| s3_key | varchar(255) | NULL | S3キー |
| model_version | varchar(50) | NULL | モデルバージョン |
| created_at | timestamp | NOT NULL | 作成日時 |
| updated_at | timestamp | NOT NULL | 更新日時 |

**インデックス**: INDEX (predicted_at DESC)

**データソース**: S3 `predictions/latest.json` (日次更新)

---

## 7. forecast_details（予測詳細データ）

| カラム | 型 | NULL | 説明 |
|-------|-----|------|------|
| id | bigint | NOT NULL | 主キー |
| forecast_run_id | bigint | NOT NULL | 予測実行ID（FK → forecast_runs） |
| company_id | bigint | NOT NULL | 銘柄ID（FK → companies） |
| current_price | decimal(10,2) | NOT NULL | 現在価格 |
| predicted_12m_price | decimal(10,2) | NOT NULL | 12ヶ月後予測価格 |
| predicted_12m_return | decimal(8,4) | NOT NULL | 12ヶ月予測リターン |
| monthly_data | jsonb | NOT NULL | 月次予測データ（JSON） |
| created_at | timestamp | NOT NULL | 作成日時 |
| updated_at | timestamp | NOT NULL | 更新日時 |

**インデックス**:
- UNIQUE (forecast_run_id, company_id)
- INDEX (predicted_12m_return)
- GIN INDEX (monthly_data)

**monthly_data JSONB構造**:
```json
[
  {"month": 1, "predicted_price": 4280.2, "log_return": -0.015, "return": 0.007},
  {"month": 2, "predicted_price": 4320.5, "log_return": -0.009, "return": 0.016},
  ...
  {"month": 12, "predicted_price": 4625.3, "log_return": 0.084, "return": 0.088}
]
```

**データソース**: S3 `predictions/latest.json` (日次更新)

---

## 外部キー制約

| 子テーブル | 子カラム | 親テーブル | ON DELETE |
|-----------|---------|-----------|-----------|
| industries | sector_id | sectors(id) | CASCADE |
| companies | sector_id | sectors(id) | SET NULL |
| companies | industry_id | industries(id) | SET NULL |
| stock_prices | company_id | companies(id) | CASCADE |
| kpi_snapshots | company_id | companies(id) | CASCADE |
| forecast_details | forecast_run_id | forecast_runs(id) | CASCADE |
| forecast_details | company_id | companies(id) | CASCADE |

---

## データ更新

| テーブル | 更新頻度 | 更新方法 |
|---------|---------|---------|
| sectors | 固定 | 手動 |
| industries | 固定 | 手動 |
| companies | 月次 | `rails import:monthly` |
| stock_prices | 日次 | `rails import:daily` |
| kpi_snapshots | 月次 | `rails import:monthly` |
| forecast_runs | 日次 | `rails import:daily` |
| forecast_details | 日次 | `rails import:daily` |

---

## 主要なクエリ例

### 最新株価取得
```sql
SELECT * FROM stock_prices
WHERE company_id = ? AND date = (SELECT MAX(date) FROM stock_prices)
```

### 最新予測取得
```sql
SELECT * FROM forecast_details
WHERE forecast_run_id = (SELECT id FROM forecast_runs ORDER BY predicted_at DESC LIMIT 1)
```

### 騰落率ランキング
```sql
SELECT c.ticker, sp.close, sp.change_pct
FROM stock_prices sp
JOIN companies c ON sp.company_id = c.id
WHERE sp.date = (SELECT MAX(date) FROM stock_prices)
ORDER BY ABS(sp.change_pct) DESC
LIMIT 10
```

### 高配当銘柄スクリーニング
```sql
SELECT c.ticker, k.dividend_yield, k.per, k.pbr
FROM kpi_snapshots k
JOIN companies c ON k.company_id = c.id
WHERE k.date = (SELECT MAX(date) FROM kpi_snapshots)
  AND k.dividend_yield > 3.0
ORDER BY k.dividend_yield DESC
```

---

## データサイズ

**現在**: 約73,568レコード、50MB未満

**初年度試算**:
- stock_prices: ~7,750行
- forecast_details: ~7,750行
- その他: ~数百行

**ストレージ**: 初年度で5〜10 MB（非常に軽量）
