# == Schema Information
#
# Table name: stock_prices
#
#  id         :bigint           not null, primary key
#  company_id :bigint           not null
#  date       :date             not null
#  open       :decimal(10, 2)
#  high       :decimal(10, 2)
#  low        :decimal(10, 2)
#  close      :decimal(10, 2)   not null
#  adj_close  :decimal(10, 2)
#  volume     :bigint
#  change_pct :decimal(8, 4)
#  created_at :datetime         not null
#  updated_at :datetime         not null
#
# Indexes
#
#  index_stock_prices_on_company_id           (company_id)
#  index_stock_prices_on_company_id_and_date  (company_id,date) UNIQUE
#  index_stock_prices_on_date                 (date)
#
# Foreign Keys
#
#  fk_rails_...  (company_id => companies.id)
#

# 株価データを管理するモデル
class StockPrice < ApplicationRecord
  belongs_to :company

  validates :date, presence: true
  validates :close, presence: true, numericality: { greater_than: 0 }
  validates :date, uniqueness: { scope: :company_id }

  scope :ordered, -> { order(date: :desc) }
  scope :latest, -> { order(date: :desc).limit(1) }
  scope :on_date, ->(date) { where(date: date) }
  scope :between, ->(start_date, end_date) { where(date: start_date..end_date).order(date: :asc) }
  scope :recent, ->(days = 30) { where('date >= ?', days.days.ago).order(date: :desc) }

  # 指定日の全ての株価データを取得する
  #
  # @param date [Date] 取得したい日付
  # @return [ActiveRecord::Relation] 株価データのコレクション
  def self.all_on_date(date)
    where(date: date).includes(:company)
  end

  # 最新の株価データの日付を取得する
  #
  # @return [Date, nil] 最新の日付
  def self.latest_date
    maximum(:date)
  end

  # 最新日の変動率が大きい銘柄を取得する
  #
  # @param limit [Integer] 取得件数
  # @return [ActiveRecord::Relation] 株価データのコレクション
  def self.top_movers(limit: 10)
    on_date(latest_date)
      .order(Arel.sql('ABS(change_pct) DESC'))
      .limit(limit)
      .includes(:company)
  end

  # 最新日の上昇率が高い銘柄を取得する
  #
  # @param limit [Integer] 取得件数
  # @return [ActiveRecord::Relation] 株価データのコレクション
  def self.top_gainers(limit: 10)
    on_date(latest_date)
      .order(change_pct: :desc)
      .limit(limit)
      .includes(:company)
  end

  # 最新日の下落率が高い銘柄を取得する
  #
  # @param limit [Integer] 取得件数
  # @return [ActiveRecord::Relation] 株価データのコレクション
  def self.top_losers(limit: 10)
    on_date(latest_date)
      .order(change_pct: :asc)
      .limit(limit)
      .includes(:company)
  end

  # 前日比の変動率を計算する
  #
  # @return [BigDecimal, nil] 変動率（％）
  def calculate_change_pct
    return nil unless close

    previous_price = company.stock_prices
                           .where('date < ?', date)
                           .order(date: :desc)
                           .first&.close

    return nil unless previous_price && previous_price > 0

    ((close - previous_price) / previous_price * 100).round(4)
  end

  # 変動率をセットする（未設定の場合のみ）
  #
  # @return [BigDecimal, nil] 設定された変動率
  def set_change_pct
    self.change_pct ||= calculate_change_pct
  end
end
