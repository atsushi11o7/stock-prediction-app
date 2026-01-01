# 株価データをJSON形式にシリアライズするクラス
class StockPriceSerializer
  # 単一の株価データをシリアライズする
  #
  # @param stock_price [StockPrice] 株価モデル
  # @return [Hash] シリアライズされたデータ
  def self.serialize(stock_price)
    {
      ticker: stock_price.company.ticker,
      name: stock_price.company.name,
      price: stock_price.close.to_f,
      changePct: stock_price.change_pct.to_f
    }
  end

  # 株価データのコレクションをシリアライズする
  #
  # @param stock_prices [ActiveRecord::Relation, Array] 株価データのコレクション
  # @return [Array<Hash>] シリアライズされたデータの配列
  def self.serialize_collection(stock_prices)
    stock_prices.map { |sp| serialize(sp) }
  end
end
