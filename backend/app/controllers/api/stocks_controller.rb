module Api
  # 株価データに関するAPIエンドポイントを提供するコントローラー
  class StocksController < Api::BaseController
    # 全銘柄のリストを取得する
    #
    # @return [Array<Hash>] 銘柄情報の配列
    def index
      companies = Company.includes(:sector, :industry).order(:code)

      render json: companies.map { |company|
        {
          ticker: company.ticker,
          code: company.code,
          name: company.name,
          sector: company.sector&.name,
          industry: company.industry&.name
        }
      }
    end

    # 指定銘柄の詳細情報を取得する
    #
    # @return [Hash] 銘柄の詳細情報
    def show
      company = Company.find_by!(ticker: params[:ticker])
      latest_price = company.latest_stock_price
      latest_kpi = company.latest_kpi
      latest_forecast = company.latest_forecast

      render json: {
        ticker: company.ticker,
        code: company.code,
        name: company.name,
        sector: company.sector&.name,
        industry: company.industry&.name,
        price: latest_price&.close&.to_f,
        changePct: latest_price&.change_pct&.to_f,
        kpi: latest_kpi ? {
          per: latest_kpi.per&.to_f,
          pbr: latest_kpi.pbr&.to_f,
          dividendYield: latest_kpi.dividend_yield&.to_f,
          marketCap: latest_kpi.market_cap&.to_f,
          roe: latest_kpi.roe&.to_f
        } : nil,
        forecast: latest_forecast ? {
          predicted12mReturn: (latest_forecast.predicted_12m_return * 100).round(2)
        } : nil
      }
    end

    # 指定銘柄の予測チャートデータを取得する
    #
    # クエリパラメータで表示期間を指定可能:
    # - years: 過去N年間のデータを取得
    # - start_date, end_date: 開始・終了年月を指定（YYYY-MM形式）
    #
    # @return [Hash] チャート表示用のデータ
    def forecast
      company = Company.find_by!(ticker: params[:ticker])
      latest_forecast = company.latest_forecast


      options = {
        years: params[:years],
        start_date: params[:start_date],
        end_date: params[:end_date]
      }.compact


      result = ForecastFormatterService.new(company, latest_forecast, options).call

      render json: result
    end

  end
end
