class CreateStockPrices < ActiveRecord::Migration[7.2]
  def change
    create_table :stock_prices do |t|
      t.references :company, null: false, foreign_key: true
      t.date :date, null: false
      t.decimal :open, precision: 10, scale: 2
      t.decimal :high, precision: 10, scale: 2
      t.decimal :low, precision: 10, scale: 2
      t.decimal :close, precision: 10, scale: 2, null: false
      t.decimal :adj_close, precision: 10, scale: 2
      t.bigint :volume
      t.decimal :change_pct, precision: 8, scale: 4

      t.timestamps
    end

    add_index :stock_prices, [:company_id, :date], unique: true
    add_index :stock_prices, :date
  end
end
