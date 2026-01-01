module Api
  # API共通の基底コントローラー
  # エラーハンドリングと共通ヘルパーメソッドを提供する
  class BaseController < ApplicationController
    rescue_from StandardError, with: :internal_server_error
    rescue_from ArgumentError, with: :bad_request
    rescue_from ActionController::ParameterMissing, with: :bad_request
    rescue_from ActiveRecord::RecordInvalid, with: :unprocessable_entity
    rescue_from ActiveRecord::RecordNotFound, with: :not_found

    private

    # 404 Not Foundレスポンスを返す
    #
    # @param exception [ActiveRecord::RecordNotFound] 例外オブジェクト
    # @return [void]
    def not_found(exception)
      render json: {
        error: 'Not Found',
        message: exception.message
      }, status: :not_found
    end

    # 400 Bad Requestレスポンスを返す
    #
    # @param exception [ArgumentError, ActionController::ParameterMissing] 例外オブジェクト
    # @return [void]
    def bad_request(exception)
      render json: {
        error: 'Bad Request',
        message: exception.message
      }, status: :bad_request
    end

    # 422 Unprocessable Entityレスポンスを返す
    #
    # @param exception [ActiveRecord::RecordInvalid] 例外オブジェクト
    # @return [void]
    def unprocessable_entity(exception)
      render json: {
        error: 'Unprocessable Entity',
        message: exception.message,
        details: exception.record&.errors&.full_messages
      }, status: :unprocessable_entity
    end

    # 500 Internal Server Errorレスポンスを返す
    #
    # @param exception [StandardError] 例外オブジェクト
    # @return [void]
    def internal_server_error(exception)
      Rails.logger.error("Internal Server Error: #{exception.class} - #{exception.message}")
      Rails.logger.error(exception.backtrace.join("\n"))

      render json: {
        error: 'Internal Server Error',
        message: Rails.env.production? ? 'An unexpected error occurred' : exception.message
      }, status: :internal_server_error
    end

    # パラメータから安全なlimit値を取得する
    #
    # @param default [Integer] デフォルト値
    # @param max [Integer] 最大値
    # @return [Integer] 1からmaxの範囲に収まるlimit値
    def safe_limit(default: ApiConstants::DEFAULT_LIMIT, max: ApiConstants::MAX_LIMIT)
      (params[:limit] || default).to_i.clamp(1, max)
    end
  end
end
