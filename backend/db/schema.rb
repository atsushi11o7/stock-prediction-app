# This file is auto-generated from the current state of the database. Instead
# of editing this file, please use the migrations feature of Active Record to
# incrementally modify your database, and then regenerate this schema definition.
#
# This file is the source Rails uses to define your schema when running `bin/rails
# db:schema:load`. When creating a new database, `bin/rails db:schema:load` tends to
# be faster and is potentially less error prone than running all of your
# migrations from scratch. Old migrations may fail to apply correctly if those
# migrations use external dependencies or application code.
#
# It's strongly recommended that you check this file into your version control system.

ActiveRecord::Schema[7.2].define(version: 2025_12_28_070000) do
  # These are extensions that must be enabled in order to support this database
  enable_extension "plpgsql"

  create_table "companies", force: :cascade do |t|
    t.string "code", null: false
    t.string "ticker", null: false
    t.string "name", null: false
    t.bigint "sector_id"
    t.bigint "industry_id"
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["code"], name: "index_companies_on_code"
    t.index ["industry_id"], name: "index_companies_on_industry_id"
    t.index ["sector_id"], name: "index_companies_on_sector_id"
    t.index ["ticker"], name: "index_companies_on_ticker", unique: true
  end

  create_table "forecast_details", force: :cascade do |t|
    t.bigint "forecast_run_id", null: false
    t.bigint "company_id", null: false
    t.decimal "current_price", precision: 10, scale: 2, null: false
    t.decimal "predicted_12m_price", precision: 10, scale: 2, null: false
    t.decimal "predicted_12m_return", precision: 8, scale: 4, null: false
    t.jsonb "monthly_data", default: [], null: false
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["company_id"], name: "index_forecast_details_on_company_id"
    t.index ["forecast_run_id", "company_id"], name: "index_forecast_details_on_forecast_run_id_and_company_id", unique: true
    t.index ["forecast_run_id"], name: "index_forecast_details_on_forecast_run_id"
    t.index ["monthly_data"], name: "index_forecast_details_on_monthly_data", using: :gin
    t.index ["predicted_12m_return"], name: "index_forecast_details_on_predicted_12m_return"
  end

  create_table "forecast_runs", force: :cascade do |t|
    t.datetime "predicted_at", null: false
    t.string "s3_key"
    t.string "model_version"
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["predicted_at"], name: "index_forecast_runs_on_predicted_at", order: :desc
  end

  create_table "industries", force: :cascade do |t|
    t.string "name", null: false
    t.bigint "sector_id", null: false
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["sector_id", "name"], name: "index_industries_on_sector_id_and_name", unique: true
    t.index ["sector_id"], name: "index_industries_on_sector_id"
  end

  create_table "kpi_snapshots", force: :cascade do |t|
    t.bigint "company_id", null: false
    t.date "date", null: false
    t.decimal "per", precision: 10, scale: 4
    t.decimal "pbr", precision: 10, scale: 4
    t.decimal "dividend_yield", precision: 8, scale: 4
    t.decimal "market_cap", precision: 15, scale: 2
    t.decimal "eps", precision: 10, scale: 2
    t.decimal "bps", precision: 10, scale: 2
    t.decimal "psr", precision: 10, scale: 4
    t.decimal "payout_ratio", precision: 8, scale: 4
    t.decimal "roe", precision: 8, scale: 4
    t.decimal "roa", precision: 8, scale: 4
    t.decimal "operating_margin", precision: 8, scale: 4
    t.decimal "net_margin", precision: 8, scale: 4
    t.decimal "equity_ratio", precision: 8, scale: 4
    t.decimal "revenue_growth", precision: 8, scale: 4
    t.decimal "earnings_growth", precision: 8, scale: 4
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["company_id", "date"], name: "index_kpi_snapshots_on_company_id_and_date", unique: true
    t.index ["company_id"], name: "index_kpi_snapshots_on_company_id"
    t.index ["date"], name: "index_kpi_snapshots_on_date"
    t.index ["dividend_yield"], name: "index_kpi_snapshots_on_dividend_yield"
    t.index ["market_cap"], name: "index_kpi_snapshots_on_market_cap"
    t.index ["roe"], name: "index_kpi_snapshots_on_roe"
  end

  create_table "sectors", force: :cascade do |t|
    t.string "name", null: false
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["name"], name: "index_sectors_on_name", unique: true
  end

  create_table "stock_prices", force: :cascade do |t|
    t.bigint "company_id", null: false
    t.date "date", null: false
    t.decimal "open", precision: 10, scale: 2
    t.decimal "high", precision: 10, scale: 2
    t.decimal "low", precision: 10, scale: 2
    t.decimal "close", precision: 10, scale: 2, null: false
    t.decimal "adj_close", precision: 10, scale: 2
    t.bigint "volume"
    t.decimal "change_pct", precision: 8, scale: 4
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["company_id", "date"], name: "index_stock_prices_on_company_id_and_date", unique: true
    t.index ["company_id"], name: "index_stock_prices_on_company_id"
    t.index ["date"], name: "index_stock_prices_on_date"
  end

  add_foreign_key "companies", "industries"
  add_foreign_key "companies", "sectors"
  add_foreign_key "forecast_details", "companies"
  add_foreign_key "forecast_details", "forecast_runs"
  add_foreign_key "industries", "sectors"
  add_foreign_key "kpi_snapshots", "companies"
  add_foreign_key "stock_prices", "companies"
end
