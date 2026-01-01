# 予測詳細データをJSON形式にシリアライズするクラス
class ForecastDetailSerializer
  # 単一の予測詳細をシリアライズする
  #
  # @param forecast_detail [ForecastDetail] 予測詳細モデル
  # @return [Hash] シリアライズされたデータ
  def self.serialize(forecast_detail)
    {
      ticker: forecast_detail.company.ticker,
      name: forecast_detail.company.name,
      currentPrice: forecast_detail.current_price.to_f,
      predicted12mPrice: forecast_detail.predicted_12m_price.to_f,
      predicted12mReturn: (forecast_detail.predicted_12m_return * 100).round(2)
    }
  end

  # 予測詳細のコレクションをシリアライズする
  #
  # @param forecast_details [ActiveRecord::Relation, Array] 予測詳細のコレクション
  # @return [Array<Hash>] シリアライズされたデータの配列
  def self.serialize_collection(forecast_details)
    forecast_details.map { |fd| serialize(fd) }
  end
end
