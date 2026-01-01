# API全体で使用する定数を定義するモジュール
module ApiConstants
  # デフォルトの取得件数
  DEFAULT_LIMIT = 10
  # 最大取得件数
  MAX_LIMIT = 50
  # マーケット変動銘柄のデフォルト取得件数
  MOVERS_DEFAULT_LIMIT = 5

  # S3上のデータファイルパス
  S3_PATHS = {
    universe: "config/universes/enrich_topix_core_30_20251031.yaml",
    daily_latest: "daily/latest.json",
    predictions_latest: "predictions/latest.json",
    daily_prefix: "daily/",
    predictions_prefix: "predictions/"
  }.freeze

  # バリュー株スクリーニングの閾値
  VALUATION_THRESHOLDS = {
    per_max: 15,
    pbr_max: 1.5,
    dividend_yield_min: 3.0,
    roe_min: 10
  }.freeze

  # グロース株スクリーニングの閾値
  GROWTH_THRESHOLDS = {
    roe_min: 15,
    growth_min: 10
  }.freeze
end
