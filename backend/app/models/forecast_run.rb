# == Schema Information
#
# Table name: forecast_runs
#
#  id            :bigint           not null, primary key
#  predicted_at  :datetime         not null
#  s3_key        :string
#  model_version :string
#  created_at    :datetime         not null
#  updated_at    :datetime         not null
#
# Indexes
#
#  index_forecast_runs_on_predicted_at  (predicted_at)
#

# 予測実行の管理を行うモデル
class ForecastRun < ApplicationRecord
  has_many :forecast_details, dependent: :destroy

  validates :predicted_at, presence: true

  scope :ordered, -> { order(predicted_at: :desc) }
  scope :latest, -> { order(predicted_at: :desc).limit(1) }
  scope :recent, ->(limit = 10) { order(predicted_at: :desc).limit(limit) }
  scope :by_model_version, ->(version) { where(model_version: version) }

  # 最新の予測実行を取得する
  #
  # @return [ForecastRun, nil] 最新の予測実行
  def self.latest_run
    order(predicted_at: :desc).first
  end

  # 指定日時以降の予測実行を取得する
  #
  # @param datetime [DateTime] 基準日時
  # @return [ActiveRecord::Relation] 予測実行のコレクション
  def self.since(datetime)
    where('predicted_at >= ?', datetime).order(predicted_at: :desc)
  end

  # 予測詳細を企業情報と共に取得する
  #
  # @return [ActiveRecord::Relation] 予測詳細のコレクション
  def details_with_companies
    forecast_details.includes(:company).order('companies.code')
  end

  # リターンが高い上位の予測を取得する
  #
  # @param limit [Integer] 取得件数
  # @return [ActiveRecord::Relation] 予測詳細のコレクション
  def top_predictions(limit: 10)
    forecast_details.includes(:company)
                   .order(predicted_12m_return: :desc)
                   .limit(limit)
  end

  # リターンが低い下位の予測を取得する
  #
  # @param limit [Integer] 取得件数
  # @return [ActiveRecord::Relation] 予測詳細のコレクション
  def bottom_predictions(limit: 10)
    forecast_details.includes(:company)
                   .order(predicted_12m_return: :asc)
                   .limit(limit)
  end

  # 予測データの統計情報を取得する
  #
  # @return [Hash] 統計情報
  #   - count: 予測件数
  #   - avg_return: 平均リターン
  #   - max_return: 最大リターン
  #   - min_return: 最小リターン
  #   - median_return: 中央値リターン
  def statistics
    details = forecast_details
    {
      count: details.count,
      avg_return: details.average(:predicted_12m_return)&.round(4),
      max_return: details.maximum(:predicted_12m_return)&.round(4),
      min_return: details.minimum(:predicted_12m_return)&.round(4),
      median_return: calculate_median_return(details)
    }
  end

  private

  # 中央値を計算する
  #
  # @param details [ActiveRecord::Relation] 予測詳細のコレクション
  # @return [Float, nil] 中央値
  def calculate_median_return(details)
    returns = details.pluck(:predicted_12m_return).compact.sort
    return nil if returns.empty?

    mid = returns.length / 2
    returns.length.odd? ? returns[mid] : (returns[mid - 1] + returns[mid]) / 2.0
  end
end
