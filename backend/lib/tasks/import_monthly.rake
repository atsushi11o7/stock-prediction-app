# S3から月次の静的データ（銘柄マスタ、KPI等）をインポートするRakeタスク
#
# 使用方法:
#   rails import:monthly
#
# 処理内容:
# 1. S3から銘柄ユニバースデータ（universe.json）を取得
# 2. セクターと業種のマスタデータを作成・更新
# 3. 企業情報を作成・更新
# 4. KPIスナップショットを保存（重複はスキップ）
namespace :import do
  desc "Import monthly static data (universe) from S3"
  task monthly: :environment do
    require "aws-sdk-s3"
    require "yaml"
    require_relative "../../lib/s3_client_helper"

    Rails.logger.info "=== Starting monthly static data import ==="
    Rails.logger.info "Timestamp: #{Time.current}"


    begin
      s3_client = S3ClientHelper.create_client
      bucket = S3ClientHelper.bucket_name
    rescue S3ClientHelper::MissingCredentialsError => e
      Rails.logger.error e.message
      puts "ERROR: #{e.message}"
      exit 1
    end

    key = ApiConstants::S3_PATHS[:universe]

    begin

      puts "Fetching #{key} from S3 bucket: #{bucket}"
      response = s3_client.get_object(bucket: bucket, key: key)
      yaml_content = response.body.read


      data = YAML.safe_load(yaml_content, permitted_classes: [Symbol, Date])
      universe = data["universe"]
      puts "Loaded #{universe.size} companies from YAML"

      updated_companies = 0
      new_companies = 0
      updated_kpis = 0
      new_kpis = 0
      new_sectors = 0
      new_industries = 0


      ActiveRecord::Base.transaction do
        universe.each_with_index do |company_data, index|
          ticker = company_data["ticker"]
          puts "[#{index + 1}/#{universe.size}] Processing #{ticker}..."


          sector = if company_data["sector"].present?
            existing_sector = Sector.find_by(name: company_data["sector"])
            if existing_sector
              existing_sector
            else
              new_sectors += 1
              Sector.create!(name: company_data["sector"])
            end
          else
            nil
          end


          industry = if company_data["industry"].present? && sector.present?
            existing_industry = Industry.find_by(name: company_data["industry"], sector: sector)
            if existing_industry
              existing_industry
            else
              new_industries += 1
              Industry.create!(name: company_data["industry"], sector: sector)
            end
          else
            nil
          end


          company = Company.find_by(ticker: ticker)

          if company

            updated = false
            if company.code != company_data["code"].to_s
              company.code = company_data["code"].to_s
              updated = true
            end
            if company.name != company_data["name"]
              company.name = company_data["name"]
              updated = true
            end
            if company.sector != sector
              company.sector = sector
              updated = true
            end
            if company.industry != industry
              company.industry = industry
              updated = true
            end

            if updated
              company.save!
              updated_companies += 1
              puts "  ✓ Updated #{company.name} (#{ticker})"
            else
              puts "  - No changes for #{company.name} (#{ticker})"
            end
          else

            company = Company.create!(
              ticker: ticker,
              code: company_data["code"].to_s,
              name: company_data["name"],
              sector: sector,
              industry: industry
            )
            new_companies += 1
            puts "  ✓ Created #{company.name} (#{ticker})"
          end


          snapshot_date = Date.today.beginning_of_month

          if company_data["PER"].present? || company_data["PBR"].present? || company_data["DividendYield"].present?
            kpi = company.kpi_snapshots.find_by(date: snapshot_date)

            if kpi

              kpi_updated = false
              if kpi.per != company_data["PER"]
                kpi.per = company_data["PER"]
                kpi_updated = true
              end
              if kpi.pbr != company_data["PBR"]
                kpi.pbr = company_data["PBR"]
                kpi_updated = true
              end
              if kpi.dividend_yield != company_data["DividendYield"]
                kpi.dividend_yield = company_data["DividendYield"]
                kpi_updated = true
              end

              if kpi_updated
                kpi.save!
                updated_kpis += 1
                puts "  ✓ Updated KPI snapshot for #{ticker}"
              else
                puts "  - No KPI changes for #{ticker}"
              end
            else

              kpi = company.kpi_snapshots.create!(
                date: snapshot_date,
                per: company_data["PER"],
                pbr: company_data["PBR"],
                dividend_yield: company_data["DividendYield"]
              )
              new_kpis += 1
              puts "  ✓ Created KPI snapshot for #{ticker}"
            end
          end
        end
      end


      puts "\n=== Monthly import completed ==="
      puts "\nCompanies:"
      puts "  Total in DB: #{Company.count}"
      puts "  New companies: #{new_companies}"
      puts "  Updated companies: #{updated_companies}"
      puts "\nSectors & Industries:"
      puts "  Total sectors: #{Sector.count} (+#{new_sectors} new)"
      puts "  Total industries: #{Industry.count} (+#{new_industries} new)"
      puts "\nKPI Snapshots:"
      puts "  Total in DB: #{KpiSnapshot.count}"
      puts "  New snapshots: #{new_kpis}"
      puts "  Updated snapshots: #{updated_kpis}"

    rescue Aws::S3::Errors::NoSuchKey
      puts "ERROR: File not found: s3://#{bucket}/#{key}"
      puts "Please check:"
      puts "  1. The universe file exists in S3"
      puts "  2. The file path is correct"
      exit 1
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

  desc "Import monthly data and show diff from current state"
  task monthly_with_diff: :environment do
    require "aws-sdk-s3"
    require "yaml"

    puts "=== Analyzing changes before import ==="


    s3_client = Aws::S3::Client.new(
      region: ENV.fetch("AWS_REGION", "ap-northeast-1"),
      access_key_id: ENV["AWS_ACCESS_KEY_ID"],
      secret_access_key: ENV["AWS_SECRET_ACCESS_KEY"]
    )

    bucket = ENV.fetch("S3_BUCKET_NAME", "stock-prediction-data")
    key = "config/universes/enrich_topix_core_30_20251031.yaml"

    begin
      response = s3_client.get_object(bucket: bucket, key: key)
      yaml_content = response.body.read
      data = YAML.safe_load(yaml_content, permitted_classes: [Symbol, Date])
      universe = data["universe"]


      new_tickers = []
      updated_data = []
      unchanged = 0

      universe.each do |company_data|
        ticker = company_data["ticker"]
        company = Company.find_by(ticker: ticker)

        if company.nil?
          new_tickers << ticker
        else
          changes = []
          changes << "code: #{company.code} → #{company_data["code"]}" if company.code != company_data["code"].to_s
          changes << "name: #{company.name} → #{company_data["name"]}" if company.name != company_data["name"]
          changes << "sector: #{company.sector&.name} → #{company_data["sector"]}" if company.sector&.name != company_data["sector"]
          changes << "industry: #{company.industry&.name} → #{company_data["industry"]}" if company.industry&.name != company_data["industry"]


          latest_kpi = company.kpi_snapshots.order(date: :desc).first
          if latest_kpi
            changes << "PER: #{latest_kpi.per} → #{company_data["PER"]}" if latest_kpi.per != company_data["PER"]
            changes << "PBR: #{latest_kpi.pbr} → #{company_data["PBR"]}" if latest_kpi.pbr != company_data["PBR"]
            changes << "DividendYield: #{latest_kpi.dividend_yield} → #{company_data["DividendYield"]}" if latest_kpi.dividend_yield != company_data["DividendYield"]
          end

          if changes.any?
            updated_data << { ticker: ticker, name: company.name, changes: changes }
          else
            unchanged += 1
          end
        end
      end


      puts "\n=== Change Summary ==="
      puts "New companies: #{new_tickers.size}"
      if new_tickers.any?
        new_tickers.each { |t| puts "  + #{t}" }
      end

      puts "\nUpdated companies: #{updated_data.size}"
      if updated_data.any?
        updated_data.each do |item|
          puts "  #{item[:ticker]} (#{item[:name]})"
          item[:changes].each { |change| puts "    - #{change}" }
        end
      end

      puts "\nUnchanged companies: #{unchanged}"

      puts "\nProceed with import? (y/n)"
      print "> "
      answer = STDIN.gets.chomp.downcase

      if answer == "y" || answer == "yes"
        puts "\nProceeding with import..."
        Rake::Task["import:monthly"].invoke
      else
        puts "Import cancelled."
      end

    rescue => e
      puts "ERROR: #{e.class} - #{e.message}"
      raise
    end
  end
end
