# == Schema Information
#
# Table name: companies
#
#  id          :bigint           not null, primary key
#  code        :string           not null
#  ticker      :string           not null
#  name        :string           not null
#  sector_id   :bigint
#  industry_id :bigint
#  created_at  :datetime         not null
#  updated_at  :datetime         not null
#
# Indexes
#
#  index_companies_on_code         (code)
#  index_companies_on_industry_id  (industry_id)
#  index_companies_on_sector_id    (sector_id)
#  index_companies_on_ticker       (ticker) UNIQUE
#
# Foreign Keys
#
#  fk_rails_...  (sector_id => sectors.id)
#  fk_rails_...  (industry_id => industries.id)
#

# 企業情報を管理するモデル
class Company < ApplicationRecord
  belongs_to :sector, optional: true
  belongs_to :industry, optional: true
  has_many :stock_prices, dependent: :destroy
  has_many :kpi_snapshots, dependent: :destroy
  has_many :forecast_details, dependent: :destroy

  validates :code, presence: true
  validates :ticker, presence: true, uniqueness: true
  validates :name, presence: true

  scope :ordered, -> { order(:code) }
  scope :by_ticker, ->(ticker) { find_by(ticker: ticker) }
  scope :by_sector, ->(sector_name) { joins(:sector).where(sectors: { name: sector_name }) }
  scope :by_industry, ->(industry_name) { joins(:industry).where(industries: { name: industry_name }) }

  # 最新の株価終値を取得する
  #
  # @return [BigDecimal, nil] 最新の終値（データがない場合はnil）
  def latest_price
    stock_prices.order(date: :desc).first&.close
  end

  # 最新の株価レコードを取得する
  #
  # @return [StockPrice, nil] 最新の株価レコード
  def latest_stock_price
    stock_prices.order(date: :desc).first
  end

  # 最新のKPIスナップショットを取得する
  #
  # @return [KpiSnapshot, nil] 最新のKPIスナップショット
  def latest_kpi
    kpi_snapshots.order(date: :desc).first
  end

  # 最新の予測データを取得する
  #
  # @return [ForecastDetail, nil] 最新の予測詳細
  def latest_forecast
    forecast_details.joins(:forecast_run)
                   .order('forecast_runs.predicted_at DESC')
                   .first
  end

  # 指定日の株価を取得する
  #
  # @param date [Date] 取得したい日付
  # @return [BigDecimal, nil] 指定日の終値
  def price_on(date)
    stock_prices.find_by(date: date)&.close
  end

  # 期間を指定して株価データを取得する
  #
  # @param start_date [Date] 開始日
  # @param end_date [Date] 終了日
  # @return [ActiveRecord::Relation] 株価データのコレクション
  def prices_between(start_date, end_date)
    stock_prices.where(date: start_date..end_date).order(date: :asc)
  end
end
