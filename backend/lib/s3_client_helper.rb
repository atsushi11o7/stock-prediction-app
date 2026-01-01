# AWS S3クライアントの生成とバケット名の管理を行うヘルパーモジュール
module S3ClientHelper
  # AWS認証情報が不足している場合に発生するエラー
  class MissingCredentialsError < StandardError; end

  # AWS S3クライアントを生成する
  #
  # @return [Aws::S3::Client] S3クライアントのインスタンス
  # @raise [MissingCredentialsError] AWS認証情報が環境変数に設定されていない場合
  def self.create_client
    begin
      Aws::S3::Client.new(
        region: ENV.fetch("AWS_REGION", "ap-northeast-1"),
        access_key_id: ENV.fetch("AWS_ACCESS_KEY_ID"),
        secret_access_key: ENV.fetch("AWS_SECRET_ACCESS_KEY")
      )
    rescue KeyError => e
      raise MissingCredentialsError, "Missing required AWS credentials: #{e.message}\nPlease set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables."
    end
  end

  # S3バケット名を取得する
  #
  # @return [String] S3バケット名
  def self.bucket_name
    ENV.fetch("S3_BUCKET_NAME", "stock-prediction-data")
  end
end
