FROM ruby:3.4.7-bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    RAILS_ENV=production \
    TZ=Asia/Tokyo \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# 必要なパッケージをインストール
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    git \
    curl \
    tzdata \
    ca-certificates \
    build-essential \
    pkg-config \
    libpq-dev \
    nodejs \
    postgresql-client \
 && rm -rf /var/lib/apt/lists/*

# アプリケーションディレクトリ
WORKDIR /app

# Gemfileをコピーして依存関係をインストール
COPY Gemfile Gemfile.lock ./
RUN bundle config set --local deployment 'true' && \
    bundle config set --local without 'development test' && \
    bundle install

# アプリケーションコードをコピー
COPY . .

# アセットのプリコンパイル（エラー回避用）
RUN bundle exec rails assets:precompile || true

EXPOSE 3000

CMD ["bundle", "exec", "rails", "server", "-b", "0.0.0.0"]
