class CreateForecastRuns < ActiveRecord::Migration[7.2]
  def change
    create_table :forecast_runs do |t|
      t.datetime :predicted_at, null: false
      t.string :s3_key
      t.string :model_version

      t.timestamps
    end

    add_index :forecast_runs, :predicted_at, order: { predicted_at: :desc }
  end
end
