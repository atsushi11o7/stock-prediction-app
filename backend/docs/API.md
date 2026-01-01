# API 仕様

Rails API エンドポイント一覧とデータ取得ガイド

**ベースURL**: `http://localhost:3000` (開発) / `http://your-server:3000` (本番)

---

## エンドポイント一覧

### 銘柄関連

#### 銘柄一覧
```
GET /api/stocks
```

**レスポンス例**:
```json
[
  {
    "ticker": "2914.T",
    "code": "2914",
    "name": "日本たばこ産業",
    "sector": "Consumer Defensive",
    "industry": "Tobacco"
  }
]
```

---

#### 銘柄詳細
```
GET /api/stocks/:ticker
```

**レスポンス例**:
```json
{
  "ticker": "7203.T",
  "name": "トヨタ自動車",
  "price": 12840.0,
  "changePct": 2.35,
  "kpi": {
    "per": 12.5,
    "pbr": 1.2,
    "dividendYield": 2.8,
    "marketCap": 45000.0,
    "roe": 8.5
  },
  "forecast": {
    "predicted12mReturn": 8.8
  }
}
```

---

#### 株価データ
```
GET /api/stocks/:ticker/prices?from=2024-01-01&to=2025-12-31
```

**レスポンス例**:
```json
[
  {
    "date": "2025-12-26",
    "open": 12800.0,
    "high": 12950.0,
    "low": 12780.0,
    "close": 12840.0,
    "volume": 15234567,
    "changePct": 2.35
  }
]
```

---

#### 予測チャートデータ
```
GET /api/stocks/:ticker/forecast
```

**レスポンス例**:
```json
{
  "ticker": "7203.T",
  "labels": ["2024-12", "2025-01", ..., "2026-11"],
  "actual": [12340, 12450, ..., 12840, null, ...],
  "predicted": [null, ..., null, 12950, 13080, ...],
  "predictStartIndex": 12
}
```

---

### マーケット関連

#### マーケット概要
```
GET /api/market/overview
```

**レスポンス例**:
```json
{
  "date": "2025-12-28",
  "totalStocks": 31,
  "advancing": 18,
  "declining": 11,
  "unchanged": 2,
  "avgChangePct": 0.52,
  "topGainer": {
    "ticker": "7203.T",
    "name": "トヨタ自動車",
    "changePct": 3.45
  },
  "topLoser": {
    "ticker": "9984.T",
    "name": "ソフトバンクグループ",
    "changePct": -2.15
  }
}
```

---

#### 騰落率ランキング
```
GET /api/market/movers?limit=5
```

**レスポンス例**:
```json
[
  {
    "ticker": "7203.T",
    "name": "トヨタ自動車",
    "price": 12840.0,
    "changePct": 2.35
  }
]
```

その他:
- `GET /api/market/gainers?limit=10` - 値上がり率上位
- `GET /api/market/losers?limit=10` - 値下がり率上位
- `GET /api/market/sectors` - セクター別パフォーマンス

---

### 予測関連

#### 最新予測一覧
```
GET /api/forecasts/latest
```

**レスポンス例**:
```json
{
  "predictedAt": "2025-12-27T23:00:00+09:00",
  "modelVersion": "best_model",
  "forecasts": [
    {
      "ticker": "2914.T",
      "name": "日本たばこ産業",
      "currentPrice": 4250.5,
      "predicted12mPrice": 4625.3,
      "predicted12mReturn": 8.8
    }
  ]
}
```

その他:
- `GET /api/forecasts/top_returns?limit=10` - 予測リターン上位
- `GET /api/forecasts/bottom_returns?limit=10` - 予測リターン下位
- `GET /api/forecasts/statistics` - 予測統計情報

---

### スクリーニング関連

#### 高配当銘柄
```
GET /api/screening/high_dividend?min_yield=3.0&limit=10
```

**レスポンス例**:
```json
[
  {
    "ticker": "2914.T",
    "name": "日本たばこ産業",
    "dividendYield": 4.5,
    "per": 52.9,
    "pbr": 2.47,
    "roe": 8.2
  }
]
```

その他:
- `GET /api/screening/low_per?max_per=15` - 低PER銘柄
- `GET /api/screening/high_roe?min_roe=10` - 高ROE銘柄
- `GET /api/screening/value_stocks` - バリュー株
- `GET /api/screening/growth_stocks` - 成長株
- `GET /api/screening/top_market_cap` - 時価総額上位

---

## 主な使用例

### ダッシュボード画面
```javascript
// マーケット概要
fetch('/api/market/overview')

// 騰落率上位5銘柄
fetch('/api/market/movers?limit=5')

// 予測リターン上位5銘柄
fetch('/api/forecasts/top_returns?limit=5')
```

### 銘柄詳細画面
```javascript
// 銘柄詳細
fetch('/api/stocks/7203.T')

// 予測チャート
fetch('/api/stocks/7203.T/forecast')

// 株価履歴
fetch('/api/stocks/7203.T/prices?from=2024-01-01')
```

### スクリーニング画面
```javascript
// 高配当銘柄
fetch('/api/screening/high_dividend?min_yield=3.0&limit=20')

// バリュー株
fetch('/api/screening/value_stocks?per_max=15&pbr_max=1.5')
```

---

## データ更新頻度

| データ種別 | 更新頻度 | 更新時刻 |
|-----------|---------|---------|
| 株価データ | 日次 | 23:00 JST |
| 予測データ | 日次 | 23:00 JST |
| KPIデータ | 月次 | 月初 |
| 企業情報 | 月次 | 月初 |

---

## エラーレスポンス

### 共通フォーマット
```json
{
  "error": "NotFound",
  "message": "Company not found with ticker: INVALID.T"
}
```

### HTTPステータスコード

| コード | 意味 | 説明 |
|-------|------|------|
| 200 | OK | リクエスト成功 |
| 400 | Bad Request | パラメータ不正 |
| 404 | Not Found | リソースが見つからない |
| 500 | Internal Server Error | サーバーエラー |

---

## CORS設定

### 許可オリジン
- 開発環境: `http://localhost:3000`, `http://localhost:3001`
- 本番環境: 環境変数 `FRONTEND_URL` で指定

### 許可メソッド
`GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `OPTIONS`, `HEAD`

---

## 認証

現在はオープンAPI（認証不要）

将来的にAPIキー認証を実装予定
