module Api
  # マーケット情報に関するAPIエンドポイントを提供するコントローラー
  class MarketController < Api::BaseController
    # 最新日の変動率が大きい銘柄を取得する
    #
    # @return [Array<Hash>] 株価データの配列
    def movers
      limit = safe_limit(default: ApiConstants::MOVERS_DEFAULT_LIMIT)

      movers = StockPrice.top_movers(limit: limit)

      render json: StockPriceSerializer.serialize_collection(movers)
    end

    # 最新日の上昇率が高い銘柄を取得する
    #
    # @return [Array<Hash>] 株価データの配列
    def gainers
      limit = safe_limit

      gainers = StockPrice.top_gainers(limit: limit)

      render json: StockPriceSerializer.serialize_collection(gainers)
    end

    # 最新日の下落率が高い銘柄を取得する
    #
    # @return [Array<Hash>] 株価データの配列
    def losers
      limit = safe_limit

      losers = StockPrice.top_losers(limit: limit)

      render json: StockPriceSerializer.serialize_collection(losers)
    end

    # マーケット全体の概要を取得する
    #
    # @return [Hash] マーケット統計情報
    def overview
      latest_date = StockPrice.latest_date
      return render json: { error: 'No data available' }, status: :not_found unless latest_date

      latest_prices = StockPrice.all_on_date(latest_date)

      stats = calculate_market_stats(latest_prices)

      render json: {
        date: latest_date.strftime("%Y-%m-%d"),
        totalStocks: latest_prices.count,
        **stats,
        topGainer: serialize_top_stock(latest_prices.max_by(&:change_pct)),
        topLoser: serialize_top_stock(latest_prices.min_by(&:change_pct))
      }
    end

    private

    # マーケット統計を計算する
    #
    # @param stock_prices [ActiveRecord::Relation] 株価データのコレクション
    # @return [Hash] 統計情報
    def calculate_market_stats(stock_prices)
      advancing = 0
      declining = 0
      unchanged = 0
      sum = 0.0

      stock_prices.each do |sp|
        pct = sp.change_pct
        next if pct.nil?

        if pct > 0
          advancing += 1
        elsif pct < 0
          declining += 1
        else
          unchanged += 1
        end
        sum += pct
      end

      count = advancing + declining + unchanged
      avg = count > 0 ? sum / count : 0.0

      {
        advancing: advancing,
        declining: declining,
        unchanged: unchanged,
        avgChangePct: avg
      }
    end

    # トップ銘柄をシリアライズする
    #
    # @param stock_price [StockPrice, nil] 株価データ
    # @return [Hash, nil] シリアライズされた銘柄データ
    def serialize_top_stock(stock_price)
      return nil unless stock_price

      {
        ticker: stock_price.company.ticker,
        name: stock_price.company.name,
        changePct: stock_price.change_pct.to_f
      }
    end
  end
end
