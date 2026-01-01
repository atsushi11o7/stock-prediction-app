# == Schema Information
#
# Table name: forecast_details
#
#  id                   :bigint           not null, primary key
#  forecast_run_id      :bigint           not null
#  company_id           :bigint           not null
#  current_price        :decimal(10, 2)   not null
#  predicted_12m_price  :decimal(10, 2)   not null
#  predicted_12m_return :decimal(8, 4)    not null
#  monthly_data         :jsonb            not null
#  created_at           :datetime         not null
#  updated_at           :datetime         not null
#
# Indexes
#
#  index_forecast_details_on_company_id                      (company_id)
#  index_forecast_details_on_forecast_run_id_and_company_id  (forecast_run_id,company_id) UNIQUE
#  index_forecast_details_on_monthly_data                    (monthly_data) USING gin
#  index_forecast_details_on_predicted_12m_return            (predicted_12m_return)
#
# Foreign Keys
#
#  fk_rails_...  (company_id => companies.id)
#  fk_rails_...  (forecast_run_id => forecast_runs.id)
#

# 予測詳細データを管理するモデル
class ForecastDetail < ApplicationRecord
  belongs_to :forecast_run
  belongs_to :company

  validates :current_price, presence: true, numericality: { greater_than: 0 }
  validates :predicted_12m_price, presence: true, numericality: { greater_than: 0 }
  validates :predicted_12m_return, presence: true
  validates :monthly_data, presence: true
  validates :company_id, uniqueness: { scope: :forecast_run_id }

  scope :ordered_by_return, -> { order(predicted_12m_return: :desc) }
  scope :positive_return, -> { where('predicted_12m_return > 0') }
  scope :negative_return, -> { where('predicted_12m_return < 0') }
  scope :high_return, ->(threshold = 10) { where('predicted_12m_return >= ?', threshold / 100.0) }

  # 最新の予測データを全て取得する
  #
  # @return [ActiveRecord::Relation] 予測詳細のコレクション
  def self.latest_forecasts
    joins(:forecast_run)
      .merge(ForecastRun.latest)
      .includes(:company)
  end

  # 指定企業の最新予測を取得する
  #
  # @param company [Company] 企業モデル
  # @return [ForecastDetail, nil] 最新の予測詳細
  def self.latest_for_company(company)
    where(company: company)
      .joins(:forecast_run)
      .order('forecast_runs.predicted_at DESC')
      .first
  end

  # 最新の予測からリターンが高い上位を取得する
  #
  # @param limit [Integer] 取得件数
  # @return [ActiveRecord::Relation] 予測詳細のコレクション
  def self.top_returns(limit: 10)
    latest_forecasts
      .order(predicted_12m_return: :desc)
      .limit(limit)
  end

  # 月次予測データの配列を取得する
  #
  # @return [Array<Hash>] 月次予測データの配列
  def monthly_predictions
    monthly_data.is_a?(Array) ? monthly_data : []
  end

  # 指定月の予測価格を取得する
  #
  # @param month [Integer] 月（1-12）
  # @return [BigDecimal, nil] 予測価格
  def predicted_price_at_month(month)
    prediction = monthly_predictions.find { |p| p['month'] == month }
    prediction&.dig('predicted_price')
  end

  # 指定月のリターンを取得する
  #
  # @param month [Integer] 月（1-12）
  # @return [BigDecimal, nil] リターン
  def return_at_month(month)
    prediction = monthly_predictions.find { |p| p['month'] == month }
    prediction&.dig('return')
  end

  # 6ヶ月後の予測価格を取得する
  #
  # @return [BigDecimal, nil] 6ヶ月後の予測価格
  def predicted_6m_price
    predicted_price_at_month(6)
  end

  # 6ヶ月後のリターンを取得する
  #
  # @return [BigDecimal, nil] 6ヶ月後のリターン
  def predicted_6m_return
    return_at_month(6)
  end

  # チャート表示用のデータを生成する
  #
  # @return [Hash] チャートデータ
  def chart_data
    {
      ticker: company.ticker,
      name: company.name,
      current_price: current_price.to_f,
      labels: (1..12).to_a,
      predicted: monthly_predictions.map { |p| p['predicted_price'].to_f },
      returns: monthly_predictions.map { |p| p['return'].to_f }
    }
  end

  # JSON形式の予測データを生成する
  #
  # @return [Hash] JSON形式の予測データ
  def to_forecast_json
    {
      ticker: company.ticker,
      name: company.name,
      current_price: current_price.to_f,
      predicted_12m_price: predicted_12m_price.to_f,
      predicted_12m_return: (predicted_12m_return * 100).round(2),
      predictions: monthly_predictions.map do |p|
        {
          month: p['month'],
          predicted_price: p['predicted_price'].to_f,
          return: (p['return'] * 100).round(2)
        }
      end
    }
  end

  # 予測の信頼度レベルを取得する
  #
  # @return [String] 信頼度レベル（'high', 'medium', 'low'）
  def confidence_level
    return 'high' if predicted_12m_return.abs < 0.1
    return 'medium' if predicted_12m_return.abs < 0.2
    'low'
  end
end
