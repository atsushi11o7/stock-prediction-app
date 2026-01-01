# 予測データと実績データを整形してフロントエンド用のチャートデータを生成するサービス
#
# @example デフォルト3年間のデータを取得
#   ForecastFormatterService.new(company, forecast).call
# @example 5年間のデータを取得
#   ForecastFormatterService.new(company, forecast, years: 5).call
# @example 期間を指定してデータを取得
#   ForecastFormatterService.new(company, forecast, start_date: '2020-01', end_date: '2023-12').call
class ForecastFormatterService
  # デフォルトの表示期間（年）
  DEFAULT_YEARS = 3
  # 予測する月数
  PREDICTION_MONTHS = 12
  # 日付フォーマット
  DATE_FORMAT = "%Y-%m".freeze

  # @param company [Company] 企業モデル
  # @param forecast_detail [ForecastDetail] 予測詳細モデル（nilの場合は実績データのみ）
  # @param options [Hash] オプション
  # @option options [Integer] :years 表示する過去の年数
  # @option options [String] :start_date 開始年月（YYYY-MM形式）
  # @option options [String] :end_date 終了年月（YYYY-MM形式）
  def initialize(company, forecast_detail, options = {})
    @company = company
    @forecast_detail = forecast_detail
    @options = options
  end

  # チャートデータを生成して返す
  #
  # @return [Hash] チャートデータ
  #   - ticker: 銘柄コード
  #   - labels: 月ラベルの配列
  #   - actual: 実績価格の配列
  #   - predicted: 予測価格の配列
  #   - historicalPredictions: 過去の予測データの配列
  #   - predictStartIndex: 予測開始位置のインデックス
  def call
    start_date, end_date = calculate_date_range
    prices = fetch_prices(start_date, end_date)

    return error_response if prices.empty?

    build_response(prices, start_date, end_date)
  end

  private

  # オプションに基づいて表示期間を計算する
  #
  # @return [Array<Date, Date>] 開始日と終了日の配列
  def calculate_date_range
    if @options[:start_date] && @options[:end_date]
      [parse_date(@options[:start_date]), parse_date(@options[:end_date])]
    elsif @options[:years]
      end_date = Date.today
      start_date = end_date - @options[:years].to_i.years
      [start_date, end_date]
    else
      end_date = Date.today
      start_date = end_date - DEFAULT_YEARS.years
      [start_date, end_date]
    end
  end

  # 文字列から日付オブジェクトを生成する
  #
  # @param date_str [String] 日付文字列（YYYY-MM形式）
  # @return [Date] 日付オブジェクト（パースに失敗した場合は今日の日付）
  def parse_date(date_str)
    year, month = date_str.split('-').map(&:to_i)
    Date.new(year, month, 1)
  rescue ArgumentError, TypeError => e
    Rails.logger.warn("Invalid date format: #{date_str}, error: #{e.message}. Using today's date.")
    Date.today
  end

  # 指定期間の株価データを取得する
  #
  # @param start_date [Date] 開始日
  # @param end_date [Date] 終了日
  # @return [ActiveRecord::Relation] 株価データのコレクション
  def fetch_prices(start_date, end_date)
    @company.stock_prices
           .where('date >= ? AND date <= ?', start_date, end_date)
           .order(date: :asc)
  end

  # レスポンスデータを構築する
  #
  # @param prices [ActiveRecord::Relation] 株価データ
  # @param start_date [Date] 開始日
  # @param end_date [Date] 終了日
  # @return [Hash] チャート表示用のレスポンスデータ
  def build_response(prices, start_date, end_date)
    {
      ticker: @company.ticker,
      labels: build_labels(start_date, end_date),
      actual: build_actual_data(prices, start_date, end_date),
      predicted: build_predicted_data(start_date, end_date),
      historicalPredictions: build_historical_predictions(start_date, end_date),
      predictStartIndex: calculate_predict_start_index(start_date, end_date)
    }
  end

  # 月ラベルの配列を生成する
  #
  # @param start_date [Date] 開始日
  # @param end_date [Date] 終了日
  # @return [Array<String>] 月ラベルの配列（YYYY-MM形式）
  def build_labels(start_date, end_date)
    labels = []

    current = Date.new(start_date.year, start_date.month, 1)
    end_month = Date.new(end_date.year, end_date.month, 1)

    while current <= end_month
      labels << current.strftime(DATE_FORMAT)
      current += 1.month
    end

    if @forecast_detail
      (1..PREDICTION_MONTHS).each do |month|
        future = end_date + month.months
        labels << future.strftime(DATE_FORMAT)
      end
    end

    labels
  end

  # 実績価格データの配列を生成する
  #
  # @param prices [ActiveRecord::Relation] 株価データ
  # @param start_date [Date] 開始日
  # @param end_date [Date] 終了日
  # @return [Array<Float, nil>] 実績価格の配列（データがない月はnil）
  def build_actual_data(prices, start_date, end_date)
    actual = []
    price_map = build_price_map(prices)

    current = Date.new(start_date.year, start_date.month, 1)
    end_month = Date.new(end_date.year, end_date.month, 1)

    while current <= end_month
      price = price_map.dig(current.year, current.month)
      actual << (price ? price.to_f : nil)
      current += 1.month
    end

    PREDICTION_MONTHS.times { actual << nil } if @forecast_detail

    actual
  end

  # 予測価格データの配列を生成する
  #
  # @param start_date [Date] 開始日
  # @param end_date [Date] 終了日
  # @return [Array<Float, nil>] 予測価格の配列
  def build_predicted_data(start_date, end_date)
    predicted = []

    current = Date.new(start_date.year, start_date.month, 1)
    end_month = Date.new(end_date.year, end_date.month, 1)

    while current <= end_month
      predicted << nil
      current += 1.month
    end

    if @forecast_detail
      monthly_predictions = @forecast_detail.monthly_predictions
      (1..PREDICTION_MONTHS).each do |month|
        prediction = monthly_predictions.find { |p| p['month'] == month }
        predicted << prediction&.dig('predicted_price')&.to_f
      end
    end

    predicted
  end

  # 過去の予測データを構築する
  #
  # @param start_date [Date] 開始日
  # @param end_date [Date] 終了日
  # @return [Array<Hash>] 過去の予測データの配列
  def build_historical_predictions(start_date, end_date)
    return [] unless @forecast_detail

    past_forecasts = @company.forecast_details
                            .where.not(id: @forecast_detail.id)
                            .joins(:forecast_run)
                            .where('forecast_runs.predicted_at >= ?', start_date)
                            .order('forecast_runs.predicted_at DESC')
                            .limit(2)

    total_months = months_between(start_date, end_date) + PREDICTION_MONTHS

    past_forecasts.map do |past_forecast|
      build_single_historical_prediction(past_forecast, start_date, total_months)
    end
  end

  # 単一の過去予測データを構築する
  #
  # @param past_forecast [ForecastDetail] 過去の予測詳細
  # @param start_date [Date] 開始日
  # @param total_months [Integer] 全月数
  # @return [Hash] 過去予測データ
  def build_single_historical_prediction(past_forecast, start_date, total_months)
    predicted_at = past_forecast.forecast_run.predicted_at.to_date

    as_of_index = months_between(start_date, predicted_at)
    as_of_index = [0, as_of_index].max

    values = Array.new(total_months, nil)
    past_forecast.monthly_predictions.each do |pred|
      index = as_of_index + pred['month']
      values[index] = pred['predicted_price'].to_f if index < total_months
    end

    {
      asOfIndex: as_of_index,
      values: values
    }
  end

  # 予測開始位置のインデックスを計算する
  #
  # @param start_date [Date] 開始日
  # @param end_date [Date] 終了日
  # @return [Integer] 予測開始インデックス
  def calculate_predict_start_index(start_date, end_date)
    months_between(start_date, end_date)
  end

  # 2つの日付間の月数を計算する
  #
  # @param start_date [Date] 開始日
  # @param end_date [Date] 終了日
  # @return [Integer] 月数
  def months_between(start_date, end_date)
    ((end_date.year - start_date.year) * 12 +
     (end_date.month - start_date.month) + 1)
  end

  # 株価データを年月でマップ化する
  #
  # @param prices [ActiveRecord::Relation] 株価データ
  # @return [Hash] {年 => {月 => 終値}}の形式のハッシュ
  def build_price_map(prices)
    map = {}
    prices.each do |price|
      map[price.date.year] ||= {}
      map[price.date.year][price.date.month] = price.close
    end
    map
  end

  # エラー時のレスポンスを生成する
  #
  # @return [Hash] エラーレスポンス
  def error_response
    {
      error: "No price data available for the specified period",
      ticker: @company.ticker,
      labels: [],
      actual: [],
      predicted: [],
      historicalPredictions: [],
      predictStartIndex: 0
    }
  end
end
