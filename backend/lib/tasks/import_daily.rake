# S3から最新の日次株価データと予測データをインポートするRakeタスク
#
# 使用方法:
#   rails import:daily
#
# 処理内容:
# 1. S3から最新の株価データ（stock_prices_latest.json）を取得
# 2. 各銘柄の株価データをデータベースに保存（重複はスキップ）
# 3. S3から最新の予測データ（predictions_latest.json）を取得
# 4. 予測実行レコードと予測詳細を保存
namespace :import do
  desc "Import daily stock prices and predictions from S3 (latest data)"
  task daily: :environment do
    require "aws-sdk-s3"
    require "json"
    require_relative "../../lib/s3_client_helper"

    Rails.logger.info "=== Starting daily data import ==="
    Rails.logger.info "Timestamp: #{Time.current}"


    begin
      s3_client = S3ClientHelper.create_client
      bucket = S3ClientHelper.bucket_name
    rescue S3ClientHelper::MissingCredentialsError => e
      Rails.logger.error e.message
      puts "ERROR: #{e.message}"
      exit 1
    end

    begin
      # ==========================================

      # ==========================================
      puts "\n[1/2] Importing daily stock prices..."

      stock_prices_key = ApiConstants::S3_PATHS[:daily_latest]
      puts "Fetching #{stock_prices_key}..."

      stock_response = s3_client.get_object(bucket: bucket, key: stock_prices_key)
      stock_data = JSON.parse(stock_response.body.read)

      as_of_date = Date.parse(stock_data["as_of"])
      symbols_count = stock_data["count"]
      symbols = stock_data["symbols"]

      puts "Data as of: #{as_of_date}"
      puts "Number of symbols: #{symbols_count}"

      imported_prices = 0
      skipped_prices = 0
      missing_companies = []

      ActiveRecord::Base.transaction do
        symbols.each do |symbol_data|
          ticker = symbol_data["ticker"]
          company = Company.find_by(ticker: ticker)

          unless company
            missing_companies << ticker
            next
          end


          existing = company.stock_prices.find_by(date: as_of_date)
          if existing
            skipped_prices += 1
            next
          end


          previous_price = company.stock_prices.order(date: :desc).first
          change_pct = if previous_price && previous_price.close.to_f > 0
            ((symbol_data["close"] - previous_price.close.to_f) / previous_price.close.to_f * 100).round(2)
          else
            0.0
          end


          stock_price = company.stock_prices.build(
            date: as_of_date,
            open: symbol_data["open"],
            high: symbol_data["high"],
            low: symbol_data["low"],
            close: symbol_data["close"],
            volume: symbol_data["volume"],
            change_pct: change_pct
          )

          if stock_price.save
            imported_prices += 1
          else
            puts "  ✗ Failed to save price for #{ticker}: #{stock_price.errors.full_messages.join(", ")}"
          end
        end
      end

      puts "✓ Stock prices imported: #{imported_prices}"
      puts "  Skipped (duplicates): #{skipped_prices}"
      puts "  Missing companies: #{missing_companies.size}" if missing_companies.any?
      if missing_companies.any?
        puts "    #{missing_companies.join(", ")}"
      end

      # ==========================================

      # ==========================================
      puts "\n[2/2] Importing predictions..."

      predictions_key = ApiConstants::S3_PATHS[:predictions_latest]
      puts "Fetching #{predictions_key}..."

      pred_response = s3_client.get_object(bucket: bucket, key: predictions_key)
      pred_data = JSON.parse(pred_response.body.read)

      pred_as_of_date = Date.parse(pred_data["as_of"])
      timestamp = Time.parse(pred_data["timestamp"])
      model_path = pred_data["model_path"]
      num_predictions = pred_data["num_predictions"]
      predictions = pred_data["predictions"]

      puts "Predictions as of: #{pred_as_of_date}"
      puts "Model: #{model_path}"
      puts "Number of predictions: #{num_predictions}"


      forecast_run = ForecastRun.create!(
        predicted_at: timestamp,
        model_version: File.basename(model_path, ".*")
      )
      puts "Created forecast run ##{forecast_run.id}"

      imported_forecasts = 0
      skipped_forecasts = 0

      ActiveRecord::Base.transaction do
        predictions.each do |pred|
          ticker = pred["ticker"]
          company = Company.find_by(ticker: ticker)

          unless company
            skipped_forecasts += 1
            next
          end


          monthly_data = pred["predictions"].map do |m|
            {
              month: m["month"],
              predicted_price: m["predicted_price"],
              log_return: m["log_return"],
              return: m["return"]
            }
          end


          forecast_detail = forecast_run.forecast_details.build(
            company: company,
            current_price: pred["current_price"],
            predicted_12m_price: pred["predicted_12m_price"],
            predicted_12m_return: pred["predicted_12m_return"],
            monthly_data: monthly_data
          )

          if forecast_detail.save
            imported_forecasts += 1
          else
            puts "  ✗ Failed to save forecast for #{ticker}: #{forecast_detail.errors.full_messages.join(", ")}"
          end
        end
      end

      puts "✓ Forecasts imported: #{imported_forecasts}"
      puts "  Skipped (missing companies): #{skipped_forecasts}"

      # ==========================================

      # ==========================================
      puts "\n=== Daily import completed ==="
      puts "Stock prices as of: #{as_of_date}"
      puts "  Imported: #{imported_prices}"
      puts "  Skipped: #{skipped_prices}"
      puts "\nPredictions as of: #{pred_as_of_date}"
      puts "  Forecast Run ID: #{forecast_run.id}"
      puts "  Imported: #{imported_forecasts}"
      puts "  Skipped: #{skipped_forecasts}"
      puts "\nTotal database state:"
      puts "  Companies: #{Company.count}"
      puts "  Stock Prices: #{StockPrice.count}"
      puts "  Forecast Runs: #{ForecastRun.count}"
      puts "  Forecast Details: #{ForecastDetail.count}"

    rescue Aws::S3::Errors::NoSuchKey => e
      puts "ERROR: File not found in S3"
      puts "Missing file: #{e.message}"
      puts "Please check:"
      puts "  1. Daily data has been uploaded to S3"
      puts "  2. File paths are correct: daily/latest.json, predictions/latest.json"
      raise
    rescue Aws::S3::Errors::ServiceError => e
      puts "ERROR: S3 access failed - #{e.message}"
      puts "Please check:"
      puts "  1. AWS credentials are set correctly"
      puts "  2. S3 bucket name is correct: #{bucket}"
      raise
    rescue => e
      puts "ERROR: #{e.class} - #{e.message}"
      puts e.backtrace.first(5).join("\n")
      raise
    end
  end

  desc "Import daily data for a specific date (YYYY-MM-DD)"
  task :daily_for_date, [:date] => :environment do |t, args|
    require "aws-sdk-s3"
    require "json"

    date_str = args[:date]
    unless date_str
      puts "ERROR: Please specify a date"
      puts "Usage: rails import:daily_for_date[2025-12-26]"
      exit 1
    end

    target_date = Date.parse(date_str)
    puts "=== Importing data for #{target_date} ==="


    s3_client = Aws::S3::Client.new(
      region: ENV.fetch("AWS_REGION", "ap-northeast-1"),
      access_key_id: ENV["AWS_ACCESS_KEY_ID"],
      secret_access_key: ENV["AWS_SECRET_ACCESS_KEY"]
    )

    bucket = ENV.fetch("S3_BUCKET_NAME", "stock-prediction-data")

    begin

      stock_prices_key = "daily/#{target_date}.json"
      puts "Fetching #{stock_prices_key}..."

      stock_response = s3_client.get_object(bucket: bucket, key: stock_prices_key)
      stock_data = JSON.parse(stock_response.body.read)

      imported_prices = 0
      skipped_prices = 0

      ActiveRecord::Base.transaction do
        stock_data["symbols"].each do |symbol_data|
          ticker = symbol_data["ticker"]
          company = Company.find_by(ticker: ticker)
          next unless company

          existing = company.stock_prices.find_by(date: target_date)
          if existing
            skipped_prices += 1
            next
          end

          previous_price = company.stock_prices.order(date: :desc).first
          change_pct = if previous_price && previous_price.close.to_f > 0
            ((symbol_data["close"] - previous_price.close.to_f) / previous_price.close.to_f * 100).round(2)
          else
            0.0
          end

          stock_price = company.stock_prices.build(
            date: target_date,
            open: symbol_data["open"],
            high: symbol_data["high"],
            low: symbol_data["low"],
            close: symbol_data["close"],
            volume: symbol_data["volume"],
            change_pct: change_pct
          )

          imported_prices += 1 if stock_price.save
        end
      end

      puts "✓ Stock prices imported: #{imported_prices} (skipped: #{skipped_prices})"


      predictions_key = "predictions/#{target_date}.json"
      puts "Fetching #{predictions_key}..."

      pred_response = s3_client.get_object(bucket: bucket, key: predictions_key)
      pred_data = JSON.parse(pred_response.body.read)

      timestamp = Time.parse(pred_data["timestamp"])
      model_path = pred_data["model_path"]

      forecast_run = ForecastRun.create!(
        predicted_at: timestamp,
        model_version: File.basename(model_path, ".*")
      )

      imported_forecasts = 0

      ActiveRecord::Base.transaction do
        pred_data["predictions"].each do |pred|
          company = Company.find_by(ticker: pred["ticker"])
          next unless company

          monthly_data = pred["predictions"].map do |m|
            {
              month: m["month"],
              predicted_price: m["predicted_price"],
              log_return: m["log_return"],
              return: m["return"]
            }
          end

          forecast_detail = forecast_run.forecast_details.build(
            company: company,
            current_price: pred["current_price"],
            predicted_12m_price: pred["predicted_12m_price"],
            predicted_12m_return: pred["predicted_12m_return"],
            monthly_data: monthly_data
          )

          imported_forecasts += 1 if forecast_detail.save
        end
      end

      puts "✓ Forecasts imported: #{imported_forecasts}"
      puts "=== Import completed for #{target_date} ==="

    rescue Aws::S3::Errors::NoSuchKey => e
      puts "ERROR: File not found: #{e.message}"
      exit 1
    rescue => e
      puts "ERROR: #{e.class} - #{e.message}"
      raise
    end
  end
end
