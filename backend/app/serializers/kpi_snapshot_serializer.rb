# KPIスナップショットをJSON形式にシリアライズするクラス
class KpiSnapshotSerializer
  # 基本的なKPIデータをシリアライズする
  #
  # @param kpi_snapshot [KpiSnapshot] KPIスナップショットモデル
  # @return [Hash] シリアライズされたデータ
  def self.serialize(kpi_snapshot)
    {
      ticker: kpi_snapshot.company.ticker,
      name: kpi_snapshot.company.name,
      per: kpi_snapshot.per&.to_f,
      pbr: kpi_snapshot.pbr&.to_f,
      dividendYield: kpi_snapshot.dividend_yield&.to_f,
      roe: kpi_snapshot.roe&.to_f
    }
  end

  # 配当利回り情報を含めてシリアライズする
  #
  # @param kpi_snapshot [KpiSnapshot] KPIスナップショットモデル
  # @return [Hash] シリアライズされたデータ
  def self.serialize_with_dividend(kpi_snapshot)
    serialize(kpi_snapshot)
  end

  # バリエーションスコアを含めてシリアライズする
  #
  # @param kpi_snapshot [KpiSnapshot] KPIスナップショットモデル
  # @return [Hash] シリアライズされたデータ
  def self.serialize_with_valuation_score(kpi_snapshot)
    serialize(kpi_snapshot).merge(
      valuationScore: kpi_snapshot.valuation_score
    )
  end

  # 成長率情報を含めてシリアライズする
  #
  # @param kpi_snapshot [KpiSnapshot] KPIスナップショットモデル
  # @return [Hash] シリアライズされたデータ
  def self.serialize_with_growth(kpi_snapshot)
    {
      ticker: kpi_snapshot.company.ticker,
      name: kpi_snapshot.company.name,
      roe: kpi_snapshot.roe&.to_f,
      revenueGrowth: kpi_snapshot.revenue_growth&.to_f,
      earningsGrowth: kpi_snapshot.earnings_growth&.to_f,
      per: kpi_snapshot.per&.to_f,
      pbr: kpi_snapshot.pbr&.to_f
    }
  end

  # 時価総額情報を含めてシリアライズする
  #
  # @param kpi_snapshot [KpiSnapshot] KPIスナップショットモデル
  # @return [Hash] シリアライズされたデータ
  def self.serialize_with_market_cap(kpi_snapshot)
    {
      ticker: kpi_snapshot.company.ticker,
      name: kpi_snapshot.company.name,
      marketCap: kpi_snapshot.market_cap&.to_f,
      per: kpi_snapshot.per&.to_f,
      pbr: kpi_snapshot.pbr&.to_f,
      roe: kpi_snapshot.roe&.to_f
    }
  end

  # KPIスナップショットのコレクションをシリアライズする
  #
  # @param kpi_snapshots [ActiveRecord::Relation, Array] KPIスナップショットのコレクション
  # @param method [Symbol] 使用するシリアライズメソッド名
  # @return [Array<Hash>] シリアライズされたデータの配列
  def self.serialize_collection(kpi_snapshots, method: :serialize)
    kpi_snapshots.map { |kpi| send(method, kpi) }
  end
end
