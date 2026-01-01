# モデル仕様書

TOPIX Core30銘柄を対象とした12ヶ月先株価予測LSTMモデルの仕様。

---

## 1. 概要

### 目的
1〜12ヶ月後の月次株価を予測するLSTMベースのモデル。

### 基本方針
- 軽量なモデル（BiLSTM + MLP）でLambda推論に対応
- 週次リサンプリングでノイズ削減、長期トレンド把握
- 毎営業日推論、月次ファインチューニング

---

## 2. 入出力

### 入力

| 種別 | 形状 | 説明 |
|------|------|------|
| 週次時系列特徴量 | (batch, 156, 23) | 156週 × 23特徴量 |
| 静的特徴量 | (batch, 6) | 銘柄ごとの固定情報 |
| 位置特徴量 | (batch, 2) | 年間サイクル性 |
| セクターID | (batch,) | Embeddingに変換 |

### 出力

| 種別 | 形状 | 説明 |
|------|------|------|
| 月次対数リターン | (batch, 12) | 1〜12ヶ月の対数リターン |

**ターゲット変数**:
```
R_nm(t) = log(P_{t+n months} / P_t)   (n = 1, 2, ..., 12)
```

**株価への復元**:
```
P̂_{t+n months} = P_t × exp(R̂_nm(t))
```

---

## 3. 週次時系列特徴量（23特徴量）

### OHLCV（5特徴量）

| 特徴量 | 説明 |
|--------|------|
| OpenWeek | 週初始値 |
| HighWeek | 週内高値 |
| LowWeek | 週内安値 |
| CloseWeek | 週末終値（調整後） |
| VolumeWeek | 週内出来高合計 |

### リターン（5特徴量）

| 特徴量 | 説明 |
|--------|------|
| RetWeek | 週次リターン |
| Ret4W | 4週累積リターン |
| Ret13W | 13週累積リターン |
| Ret26W | 26週累積リターン |
| Ret52W | 52週累積リターン |

### 移動平均（3特徴量）

| 特徴量 | 説明 |
|--------|------|
| MA_4W | 4週移動平均 |
| MA_13W | 13週移動平均 |
| MA_26W | 26週移動平均 |

### トレンド位置（3特徴量）

| 特徴量 | 説明 |
|--------|------|
| PriceVsMA_4W | CloseWeek / MA_4W - 1 |
| PriceVsMA_13W | CloseWeek / MA_13W - 1 |
| PriceVsMA_26W | CloseWeek / MA_26W - 1 |

### 高値安値位置（2特徴量）

| 特徴量 | 説明 |
|--------|------|
| PriceVs52WH | CloseWeek / 52週高値 - 1 |
| PriceVs52WL | CloseWeek / 52週安値 - 1 |

### ボラティリティ（2特徴量）

| 特徴量 | 説明 |
|--------|------|
| Vol_13W | 直近13週のRetWeek標準偏差 |
| Vol_26W | 直近26週のRetWeek標準偏差 |

### 出来高（1特徴量）

| 特徴量 | 説明 |
|--------|------|
| VolumeRatio | VolumeWeek / 13週平均Volume |

### ローソク足形状（2特徴量）

| 特徴量 | 説明 |
|--------|------|
| BodyRatio | \|Close - Open\| / (High - Low) |
| ClosePosInRange | (Close - Low) / (High - Low) |

---

## 4. 静的特徴量（6特徴量）

### 長期統計（3特徴量）- 価格データから計算

| 特徴量 | 説明 |
|--------|------|
| LongTermMeanRet | 過去3年のRetWeek平均 |
| LongTermVol | 過去3年のRetWeek標準偏差 |
| LongTermMaxDD | 過去3年の最大ドローダウン |

### バリュエーション（3特徴量）- yfinanceから取得

| 特徴量 | 説明 |
|--------|------|
| PER | 株価収益率 |
| PBR | 株価純資産倍率 |
| DividendYield | 配当利回り |

---

## 5. 位置特徴量（2特徴量）

| 特徴量 | 説明 |
|--------|------|
| sin_week | sin(2π × 週番号 / 52) |
| cos_week | cos(2π × 週番号 / 52) |

年間サイクル性を捉えるためのsin/cos変換。

---

## 6. モデルアーキテクチャ

```
入力:
  - weekly_seq: (batch, 156, 23)
  - static_features: (batch, 6)
  - position_features: (batch, 2)
  - sector_id: (batch,)
        │
        ▼
┌─────────────────────────────────┐
│         BiLSTM                  │
│  hidden_size: 128               │
│  num_layers: 2                  │
│  dropout: 0.2                   │
│  → (batch, 256)                 │
└─────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────┐
│      Sector Embedding           │
│  num_sectors: 9                 │
│  embedding_dim: 8               │
│  → (batch, 8)                   │
└─────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────┐
│         Concat                  │
│  [BiLSTM, Static, Position,     │
│   SectorEmb]                    │
│  → (batch, 256+6+2+8 = 272)     │
└─────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────┐
│          MLP Head               │
│  256 → 128 → 64 → 12            │
│  BatchNorm + ReLU + Dropout(0.3)│
│  → (batch, 12)                  │
└─────────────────────────────────┘
        │
        ▼
出力: [R1m, R2m, ..., R12m]（対数リターン）
```

### モデルサイズ

- パラメータ数: 約664,000
- ONNX サイズ: 約2.5MB

---

## 7. 学習設定

### データ分割

| 分割 | 比率 | 説明 |
|------|------|------|
| Train | 70% | 学習用 |
| Val | 15% | 検証用（Early Stopping） |
| Test | 15% | テスト用 |

時系列分割（データリーク防止）。

### 最適化

| 項目 | 値 |
|------|-----|
| Optimizer | AdamW |
| Learning Rate | 0.001 |
| Weight Decay | 1e-5 |
| Scheduler | ReduceLROnPlateau |
| Loss | MSE |

### Early Stopping

- patience: 15エポック
- monitor: val_loss

---

## 8. ファインチューニング

### データサンプリング

| 期間 | 比率 | 説明 |
|------|------|------|
| 直近1ヶ月 | 67% | 最新トレンドを重視 |
| 過去データ | 33% | ランダムサンプリング |

### パラメータ

| 項目 | 値 |
|------|-----|
| Learning Rate | 0.0001 (1/10) |
| Epochs | 3-5 |
| Batch Size | 32 |

---

## 9. 推論

### 処理フロー

1. Universe YAMLから銘柄リストを取得
2. 各銘柄について:
   - 日次データから週次特徴量を計算（156週）
   - 静的特徴量を計算（6特徴）
   - 位置特徴量を計算（2特徴）
   - セクターIDを取得
3. ONNX推論を実行
4. 対数リターンを株価に変換

### 出力形式

```json
{
  "timestamp": "2025-12-20T23:00:00",
  "predictions": [
    {
      "ticker": "2914.T",
      "as_of_date": "2025-12-20",
      "current_price": 4250.5,
      "predictions": [
        {"month": 1, "predicted_price": 4280.2, "return": 0.007},
        {"month": 2, "predicted_price": 4310.5, "return": 0.014},
        ...
        {"month": 12, "predicted_price": 4625.3, "return": 0.088}
      ],
      "sector": "Consumer Defensive"
    }
  ]
}
```

---

## 10. データ更新頻度

| データ種別 | 更新頻度 | 取得方法 |
|------------|----------|----------|
| 日次OHLCV | 毎営業日 | yfinance |
| バリュエーション | 月1回 | yfinance (ticker.info) |
| 静的特徴量（長期統計） | 月1回 | 週次バーから計算 |
| セクターマスタ | 年1回 | 手動更新 |

---

## 11. 制約・注意事項

### データリーケージ防止
- 静的特徴量は「基準日時点で利用可能な情報のみ」で計算
- 時系列分割でTrain/Val/Testを分離

### 生存者バイアス
- Core30は「現在の」構成銘柄
- 過去に脱落した銘柄は含まれない

### 拡張性
- TOPIX依存の特徴量は使用しない（他銘柄への拡張を考慮）
- 銘柄固有データ + セクター情報のみで予測

---

## 関連ドキュメント

- [README.md](../README.md) - システム概要
- [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - 実装サマリ
- [config/README.md](../config/README.md) - 設定ファイルガイド
