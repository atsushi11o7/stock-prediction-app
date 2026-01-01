class CreateKpiSnapshots < ActiveRecord::Migration[7.2]
  def change
    create_table :kpi_snapshots do |t|
      t.references :company, null: false, foreign_key: true
      t.date :date, null: false

      # Valuation metrics
      t.decimal :per, precision: 10, scale: 4
      t.decimal :pbr, precision: 10, scale: 4
      t.decimal :dividend_yield, precision: 8, scale: 4
      t.decimal :market_cap, precision: 15, scale: 2
      t.decimal :eps, precision: 10, scale: 2
      t.decimal :bps, precision: 10, scale: 2
      t.decimal :psr, precision: 10, scale: 4
      t.decimal :payout_ratio, precision: 8, scale: 4

      # Profitability metrics
      t.decimal :roe, precision: 8, scale: 4
      t.decimal :roa, precision: 8, scale: 4
      t.decimal :operating_margin, precision: 8, scale: 4
      t.decimal :net_margin, precision: 8, scale: 4

      # Financial health metrics
      t.decimal :equity_ratio, precision: 8, scale: 4

      # Growth metrics
      t.decimal :revenue_growth, precision: 8, scale: 4
      t.decimal :earnings_growth, precision: 8, scale: 4

      t.timestamps
    end

    add_index :kpi_snapshots, [:company_id, :date], unique: true
    add_index :kpi_snapshots, :date
    add_index :kpi_snapshots, :market_cap
    add_index :kpi_snapshots, :roe
    add_index :kpi_snapshots, :dividend_yield
  end
end
