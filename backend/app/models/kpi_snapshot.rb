# == Schema Information
#
# Table name: kpi_snapshots
#
#  id               :bigint           not null, primary key
#  company_id       :bigint           not null
#  date             :date             not null
#  per              :decimal(10, 4)
#  pbr              :decimal(10, 4)
#  dividend_yield   :decimal(8, 4)
#  market_cap       :decimal(15, 2)
#  eps              :decimal(10, 2)
#  bps              :decimal(10, 2)
#  psr              :decimal(10, 4)
#  payout_ratio     :decimal(8, 4)
#  roe              :decimal(8, 4)
#  roa              :decimal(8, 4)
#  operating_margin :decimal(8, 4)
#  net_margin       :decimal(8, 4)
#  equity_ratio     :decimal(8, 4)
#  revenue_growth   :decimal(8, 4)
#  earnings_growth  :decimal(8, 4)
#  created_at       :datetime         not null
#  updated_at       :datetime         not null
#
# Indexes
#
#  index_kpi_snapshots_on_company_id           (company_id)
#  index_kpi_snapshots_on_company_id_and_date  (company_id,date) UNIQUE
#  index_kpi_snapshots_on_date                 (date)
#  index_kpi_snapshots_on_dividend_yield       (dividend_yield)
#  index_kpi_snapshots_on_market_cap           (market_cap)
#  index_kpi_snapshots_on_roe                  (roe)
#
# Foreign Keys
#
#  fk_rails_...  (company_id => companies.id)
#

# 企業のKPI（財務指標）スナップショットを管理するモデル
class KpiSnapshot < ApplicationRecord
  belongs_to :company

  validates :date, presence: true
  validates :date, uniqueness: { scope: :company_id }

  scope :ordered, -> { order(date: :desc) }
  scope :latest, -> { order(date: :desc).limit(1) }
  scope :on_date, ->(date) { where(date: date) }

  # 最新のKPIデータの日付を取得する
  #
  # @return [Date, nil] 最新の日付
  def self.latest_date
    maximum(:date)
  end

  # 最新日の全KPIスナップショットを取得する
  #
  # @return [ActiveRecord::Relation] KPIスナップショットのコレクション
  def self.latest_snapshots
    where(date: latest_date).includes(:company)
  end

  # 配当利回りが高い銘柄を取得する
  #
  # @param min_yield [Float] 最小配当利回り（％）
  # @param limit [Integer] 取得件数
  # @return [ActiveRecord::Relation] KPIスナップショットのコレクション
  def self.high_dividend(min_yield: 3.0, limit: 10)
    latest_snapshots
      .where('dividend_yield >= ?', min_yield)
      .order(dividend_yield: :desc)
      .limit(limit)
  end

  # PERが低い銘柄を取得する
  #
  # @param max_per [Float] 最大PER
  # @param limit [Integer] 取得件数
  # @return [ActiveRecord::Relation] KPIスナップショットのコレクション
  def self.low_per(max_per: 15, limit: 10)
    latest_snapshots
      .where('per <= ? AND per > 0', max_per)
      .order(per: :asc)
      .limit(limit)
  end

  # ROEが高い銘柄を取得する
  #
  # @param min_roe [Float] 最小ROE（％）
  # @param limit [Integer] 取得件数
  # @return [ActiveRecord::Relation] KPIスナップショットのコレクション
  def self.high_roe(min_roe: 10, limit: 10)
    latest_snapshots
      .where('roe >= ?', min_roe)
      .order(roe: :desc)
      .limit(limit)
  end

  # 時価総額が高い銘柄を取得する
  #
  # @param limit [Integer] 取得件数
  # @return [ActiveRecord::Relation] KPIスナップショットのコレクション
  def self.top_market_cap(limit: 10)
    latest_snapshots
      .where.not(market_cap: nil)
      .order(market_cap: :desc)
      .limit(limit)
  end

  # バリュー株を検索する
  #
  # @param per_max [Float] 最大PER
  # @param pbr_max [Float] 最大PBR
  # @param dividend_min [Float] 最小配当利回り（％）
  # @param limit [Integer] 取得件数
  # @return [ActiveRecord::Relation] KPIスナップショットのコレクション
  def self.value_stocks(per_max: 15, pbr_max: 1.5, dividend_min: 2.5, limit: 10)
    latest_snapshots
      .where('per <= ? AND per > 0', per_max)
      .where('pbr <= ? AND pbr > 0', pbr_max)
      .where('dividend_yield >= ?', dividend_min)
      .order(dividend_yield: :desc)
      .limit(limit)
  end

  # グロース株を検索する
  #
  # @param roe_min [Float] 最小ROE（％）
  # @param growth_min [Float] 最小成長率（％）
  # @param limit [Integer] 取得件数
  # @return [ActiveRecord::Relation] KPIスナップショットのコレクション
  def self.growth_stocks(roe_min: 15, growth_min: 10, limit: 10)
    latest_snapshots
      .where('roe >= ?', roe_min)
      .where('revenue_growth >= ? OR earnings_growth >= ?', growth_min, growth_min)
      .order(roe: :desc)
      .limit(limit)
  end

  # バリエーションスコアを計算する
  #
  # @return [Integer] スコア（0-4）
  def valuation_score
    thresholds = ApiConstants::VALUATION_THRESHOLDS
    score = 0
    score += 1 if per.present? && per < thresholds[:per_max]
    score += 1 if pbr.present? && pbr < thresholds[:pbr_max]
    score += 1 if dividend_yield.present? && dividend_yield >= thresholds[:dividend_yield_min]
    score += 1 if roe.present? && roe >= thresholds[:roe_min]
    score
  end

  # 財務健全性スコアを計算する
  #
  # @return [Integer] スコア（0-3）
  def financial_health_score
    score = 0
    score += 1 if equity_ratio.present? && equity_ratio >= 40
    score += 1 if roe.present? && roe >= 8
    score += 1 if roa.present? && roa >= 5
    score
  end
end
