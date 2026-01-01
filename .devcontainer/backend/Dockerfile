# .devcontainer/backend/Dockerfile
FROM ruby:3.4.7-bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    RAILS_ENV=development \
    TZ=Asia/Tokyo \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# Railsで必要な基本ツール＋pg用ヘッダ
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    git \
    curl \
    tzdata \
    ca-certificates \
    tree \
    build-essential \
    pkg-config \
    libpq-dev \
    nodejs \
    postgresql-client \
 && rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash rails && mkdir -p /workspace && chown -R rails:rails /workspace
WORKDIR /workspace
USER rails

EXPOSE 3000