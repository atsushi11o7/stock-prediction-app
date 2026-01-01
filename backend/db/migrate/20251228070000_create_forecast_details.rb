class CreateForecastDetails < ActiveRecord::Migration[7.2]
  def change
    create_table :forecast_details do |t|
      t.references :forecast_run, null: false, foreign_key: true
      t.references :company, null: false, foreign_key: true
      t.decimal :current_price, precision: 10, scale: 2, null: false
      t.decimal :predicted_12m_price, precision: 10, scale: 2, null: false
      t.decimal :predicted_12m_return, precision: 8, scale: 4, null: false
      t.jsonb :monthly_data, null: false, default: []

      t.timestamps
    end

    add_index :forecast_details, [:forecast_run_id, :company_id], unique: true
    add_index :forecast_details, :predicted_12m_return
    add_index :forecast_details, :monthly_data, using: :gin
  end
end
