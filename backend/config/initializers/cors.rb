# CORS（Cross-Origin Resource Sharing）の設定
#
# フロントエンドアプリケーションからのAPI呼び出しを許可するための設定
# 開発環境とプロダクション環境で異なるオリジンを許可する

Rails.application.config.middleware.insert_before 0, Rack::Cors do
  # 開発環境用の設定
  allow do
    origins "http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000"

    resource "*",
      headers: :any,
      methods: [:get, :post, :put, :patch, :delete, :options, :head],
      credentials: true
  end

  # プロダクション環境用の設定（環境変数から読み込み）
  allow do
    origins ENV.fetch("FRONTEND_URL", "").split(",").map(&:strip)

    resource "*",
      headers: :any,
      methods: [:get, :post, :put, :patch, :delete, :options, :head],
      credentials: true
  end if ENV["FRONTEND_URL"].present?
end
