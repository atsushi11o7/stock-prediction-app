# .devcontainer/frontend/Dockerfile

FROM node:24-bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive \
    NODE_ENV=development \
    NEXT_TELEMETRY_DISABLED=1 \
    TZ=Asia/Tokyo \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    npm_config_update_notifier=false

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    git \
    curl \
    tzdata \
    ca-certificates \
    tree \
    procps \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

RUN mkdir -p /workspace && chown -R node:node /workspace

USER node

EXPOSE 3000 6006 9229