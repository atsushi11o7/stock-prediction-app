# S3から過去全ての日次株価データをインポートするRakeタスク（初期セットアップ用）
#
# 使用方法:
#   rails import:historical
#
# 処理内容:
# 1. S3から過去10年分の株価データファイルリストを取得
# 2. 各ファイルから日次株価データを読み込み
# 3. データベースにバルクインサート（重複はスキップ）
# 4. 進捗状況を表示しながら処理
#
# 注意: 初回セットアップ時のみ実行。通常運用ではimport:dailyを使用すること
namespace :import do
  desc "Import all historical daily data from S3 (initial setup)"
  task historical: :environment do
    require "aws-sdk-s3"
    require "json"
    require "date"
    require_relative "../../lib/s3_client_helper"

    Rails.logger.info "=== Starting historical data import ==="
    Rails.logger.info "This will import ALL daily stock prices and predictions from S3"
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
      puts "\n[1/2] Importing all historical stock prices..."



      daily_prefix = ApiConstants::S3_PATHS[:daily_prefix]
      puts "Listing files in s3://#{bucket}/#{daily_prefix}"

      all_daily_objects = []
      continuation_token = nil

      loop do
        params = { bucket: bucket, prefix: daily_prefix, max_keys: 1000 }
        params[:continuation_token] = continuation_token if continuation_token

        response = s3_client.list_objects_v2(params)
        all_daily_objects.concat(response.contents)

        break unless response.is_truncated
        continuation_token = response.next_continuation_token
      end

      daily_files = all_daily_objects
        .select { |obj| obj.key.end_with?(".json") && !obj.key.end_with?("latest.json") }
        .sort_by { |obj| obj.key }

      puts "Found #{daily_files.size} daily files"

      if daily_files.empty?
        puts "WARNING: No daily files found in daily/"
        puts "Skipping stock prices import"
      else
        total_imported_prices = 0
        total_skipped_prices = 0
        files_processed = 0

        daily_files.each_with_index do |obj, index|
          key = obj.key
          date_str = File.basename(key, ".json")

          begin
            target_date = Date.parse(date_str)
          rescue ArgumentError
            puts "  ⚠ Skipping invalid filename: #{key}"
            next
          end

          puts "\n[#{index + 1}/#{daily_files.size}] Processing #{target_date}..."


          stock_response = s3_client.get_object(bucket: bucket, key: key)
          stock_data = JSON.parse(stock_response.body.read)

          imported_prices = 0
          skipped_prices = 0

          stock_data["symbols"].each do |symbol_data|
            ticker = symbol_data["ticker"]
            company = Company.find_by(ticker: ticker)
            next unless company


            existing = company.stock_prices.find_by(date: target_date)
            if existing
              skipped_prices += 1
              next
            end


            previous_price = company.stock_prices.where("date < ?", target_date).order(date: :desc).first
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

            if stock_price.save
              imported_prices += 1
            else
              puts "    ✗ Failed to save price for #{ticker}: #{stock_price.errors.full_messages.join(", ")}"
            end
          end

          total_imported_prices += imported_prices
          total_skipped_prices += skipped_prices
          files_processed += 1

          puts "  ✓ Imported #{imported_prices} prices (skipped #{skipped_prices} duplicates)"


          if (index + 1) % 10 == 0
            puts "\n  Progress: #{index + 1}/#{daily_files.size} files processed"
            puts "  Total imported so far: #{total_imported_prices}"
          end
        end

        puts "\n✓ Stock prices import completed"
        puts "  Files processed: #{files_processed}"
        puts "  Total imported: #{total_imported_prices}"
        puts "  Total skipped: #{total_skipped_prices}"
      end

      # ==========================================

      # ==========================================
      puts "\n[2/2] Importing all historical predictions..."



      predictions_prefix = ApiConstants::S3_PATHS[:predictions_prefix]
      puts "Listing files in s3://#{bucket}/#{predictions_prefix}"

      all_prediction_objects = []
      continuation_token = nil

      loop do
        params = { bucket: bucket, prefix: predictions_prefix, max_keys: 1000 }
        params[:continuation_token] = continuation_token if continuation_token

        pred_response = s3_client.list_objects_v2(params)
        all_prediction_objects.concat(pred_response.contents)

        break unless pred_response.is_truncated
        continuation_token = pred_response.next_continuation_token
      end

      prediction_files = all_prediction_objects
        .select { |obj| obj.key.end_with?(".json") && !obj.key.end_with?("latest.json") }
        .sort_by { |obj| obj.key }

      puts "Found #{prediction_files.size} prediction files"

      if prediction_files.empty?
        puts "WARNING: No prediction files found in predictions/"
        puts "Skipping predictions import"
      else
        total_imported_forecasts = 0
        total_forecast_runs = 0

        prediction_files.each_with_index do |obj, index|
          key = obj.key
          date_str = File.basename(key, ".json")

          begin
            target_date = Date.parse(date_str)
          rescue ArgumentError
            puts "  ⚠ Skipping invalid filename: #{key}"
            next
          end

          puts "\n[#{index + 1}/#{prediction_files.size}] Processing predictions for #{target_date}..."


          pred_file_response = s3_client.get_object(bucket: bucket, key: key)
          pred_data = JSON.parse(pred_file_response.body.read)

          timestamp = Time.parse(pred_data["timestamp"])
          model_path = pred_data["model_path"]


          forecast_run = ForecastRun.create!(
            predicted_at: timestamp,
            model_version: File.basename(model_path, ".*")
          )
          total_forecast_runs += 1

          imported_forecasts = 0

          pred_data["predictions"].each do |pred|
            ticker = pred["ticker"]
            company = Company.find_by(ticker: ticker)
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

            if forecast_detail.save
              imported_forecasts += 1
            else
              puts "    ✗ Failed to save forecast for #{ticker}: #{forecast_detail.errors.full_messages.join(", ")}"
            end
          end

          total_imported_forecasts += imported_forecasts
          puts "  ✓ Created forecast run ##{forecast_run.id} with #{imported_forecasts} forecasts"


          if (index + 1) % 10 == 0
            puts "\n  Progress: #{index + 1}/#{prediction_files.size} files processed"
            puts "  Total forecast runs created: #{total_forecast_runs}"
            puts "  Total forecasts imported: #{total_imported_forecasts}"
          end
        end

        puts "\n✓ Predictions import completed"
        puts "  Files processed: #{prediction_files.size}"
        puts "  Total forecast runs: #{total_forecast_runs}"
        puts "  Total forecasts: #{total_imported_forecasts}"
      end

      # ==========================================

      # ==========================================
      puts "\n=== Historical import completed ==="
      puts "\nFinal database state:"
      puts "  Companies: #{Company.count}"
      puts "  Sectors: #{Sector.count}"
      puts "  Industries: #{Industry.count}"
      puts "  Stock Prices: #{StockPrice.count}"
      puts "  KPI Snapshots: #{KpiSnapshot.count}"
      puts "  Forecast Runs: #{ForecastRun.count}"
      puts "  Forecast Details: #{ForecastDetail.count}"


      if StockPrice.any?
        earliest_price = StockPrice.minimum(:date)
        latest_price = StockPrice.maximum(:date)
        puts "\nStock price data range:"
        puts "  Earliest: #{earliest_price}"
        puts "  Latest: #{latest_price}"
      end

      if ForecastRun.any?
        earliest_forecast = ForecastRun.minimum(:predicted_at)
        latest_forecast = ForecastRun.maximum(:predicted_at)
        puts "\nForecast data range:"
        puts "  Earliest: #{earliest_forecast}"
        puts "  Latest: #{latest_forecast}"
      end

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

  desc "Import all data (initial setup): universe → historical data"
  task initial_setup: :environment do
    puts "=== Starting initial data setup ==="
    puts "This will import: universe → historical stock prices → historical predictions"
    puts "\n"


    puts "Step 1/2: Importing universe data..."
    Rake::Task["import:monthly"].invoke
    puts "\n" + "=" * 60 + "\n\n"


    puts "Step 2/2: Importing historical data..."
    Rake::Task["import:historical"].invoke
    puts "\n" + "=" * 60 + "\n\n"

    puts "=== Initial setup completed ==="
    puts "\nNext steps:"
    puts "  1. Set up daily cron job: rails import:daily"
    puts "  2. Set up monthly cron job: rails import:monthly"
    puts "  3. Start Rails server: rails server"
  end
end
