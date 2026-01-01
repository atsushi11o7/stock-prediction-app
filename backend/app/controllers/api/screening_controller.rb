module Api
  # スクリーニング機能に関するAPIエンドポイントを提供するコントローラー
  class ScreeningController < Api::BaseController
    # 配当利回りが高い銘柄を取得する
    #
    # @return [Array<Hash>] KPIスナップショットの配列
    def high_dividend
      min_yield = params[:min_yield]&.to_f || ApiConstants::VALUATION_THRESHOLDS[:dividend_yield_min]
      limit = safe_limit

      stocks = KpiSnapshot.high_dividend(min_yield: min_yield, limit: limit)

      render json: KpiSnapshotSerializer.serialize_collection(stocks, method: :serialize_with_dividend)
    end

    # PERが低い銘柄を取得する
    #
    # @return [Array<Hash>] KPIスナップショットの配列
    def low_per
      max_per = params[:max_per]&.to_f || ApiConstants::VALUATION_THRESHOLDS[:per_max]
      limit = safe_limit

      stocks = KpiSnapshot.low_per(max_per: max_per, limit: limit)

      render json: KpiSnapshotSerializer.serialize_collection(stocks)
    end

    # ROEが高い銘柄を取得する
    #
    # @return [Array<Hash>] KPIスナップショットの配列
    def high_roe
      min_roe = params[:min_roe]&.to_f || ApiConstants::VALUATION_THRESHOLDS[:roe_min]
      limit = safe_limit

      stocks = KpiSnapshot.high_roe(min_roe: min_roe, limit: limit)

      render json: KpiSnapshotSerializer.serialize_collection(stocks)
    end

    # バリュー株を検索する
    #
    # @return [Array<Hash>] KPIスナップショットの配列
    def value_stocks
      per_max = params[:per_max]&.to_f || ApiConstants::VALUATION_THRESHOLDS[:per_max]
      pbr_max = params[:pbr_max]&.to_f || ApiConstants::VALUATION_THRESHOLDS[:pbr_max]
      dividend_min = params[:dividend_min]&.to_f || 2.5
      limit = safe_limit

      stocks = KpiSnapshot.value_stocks(
        per_max: per_max,
        pbr_max: pbr_max,
        dividend_min: dividend_min,
        limit: limit
      )

      render json: KpiSnapshotSerializer.serialize_collection(stocks, method: :serialize_with_valuation_score)
    end

    # グロース株を検索する
    #
    # @return [Array<Hash>] KPIスナップショットの配列
    def growth_stocks
      roe_min = params[:roe_min]&.to_f || ApiConstants::GROWTH_THRESHOLDS[:roe_min]
      growth_min = params[:growth_min]&.to_f || ApiConstants::GROWTH_THRESHOLDS[:growth_min]
      limit = safe_limit

      stocks = KpiSnapshot.growth_stocks(
        roe_min: roe_min,
        growth_min: growth_min,
        limit: limit
      )

      render json: KpiSnapshotSerializer.serialize_collection(stocks, method: :serialize_with_growth)
    end

    # 時価総額が高い銘柄を取得する
    #
    # @return [Array<Hash>] KPIスナップショットの配列
    def top_market_cap
      limit = safe_limit

      stocks = KpiSnapshot.top_market_cap(limit: limit)

      render json: KpiSnapshotSerializer.serialize_collection(stocks, method: :serialize_with_market_cap)
    end
  end
end
