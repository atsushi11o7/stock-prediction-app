module Api
  # 予測データに関するAPIエンドポイントを提供するコントローラー
  class ForecastsController < Api::BaseController
    # 最新の予測データを全て取得する
    #
    # @return [Hash] 予測実行情報と予測データの配列
    def latest
      latest_run = ForecastRun.latest_run

      unless latest_run
        return render json: {
          error: 'No forecast available',
          message: 'No forecast data found'
        }, status: :not_found
      end

      forecasts = latest_run.forecast_details.includes(:company).order('companies.code')

      render json: {
        predictedAt: latest_run.predicted_at.iso8601,
        modelVersion: latest_run.model_version,
        forecasts: ForecastDetailSerializer.serialize_collection(forecasts)
      }
    end

    # 最新の予測からリターンが高い上位を取得する
    #
    # @return [Array<Hash>] 予測データの配列
    def top_returns
      limit = safe_limit

      latest_run = ForecastRun.latest_run
      return render json: { error: 'No forecast available' }, status: :not_found unless latest_run

      top_forecasts = latest_run.top_predictions(limit: limit)

      render json: ForecastDetailSerializer.serialize_collection(top_forecasts)
    end

    # 最新の予測からリターンが低い下位を取得する
    #
    # @return [Array<Hash>] 予測データの配列
    def bottom_returns
      limit = safe_limit

      latest_run = ForecastRun.latest_run
      return render json: { error: 'No forecast available' }, status: :not_found unless latest_run

      bottom_forecasts = latest_run.bottom_predictions(limit: limit)

      render json: ForecastDetailSerializer.serialize_collection(bottom_forecasts)
    end

    # 最新の予測データの統計情報を取得する
    #
    # @return [Hash] 統計情報
    def statistics
      latest_run = ForecastRun.latest_run
      return render json: { error: 'No forecast available' }, status: :not_found unless latest_run

      stats = latest_run.statistics

      render json: {
        predictedAt: latest_run.predicted_at.iso8601,
        modelVersion: latest_run.model_version,
        statistics: {
          count: stats[:count],
          avgReturn: (stats[:avg_return] * 100).round(2),
          maxReturn: (stats[:max_return] * 100).round(2),
          minReturn: (stats[:min_return] * 100).round(2),
          medianReturn: (stats[:median_return] * 100).round(2)
        }
      }
    end
  end
end
