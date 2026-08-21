# syntax=docker/dockerfile:1.7

FROM node:20-bookworm-slim AS web-builder
WORKDIR /build
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY apps/web ./apps/web
RUN npm run build

FROM node:20-bookworm-slim AS control-builder
WORKDIR /build/apps/worker-control
COPY apps/worker-control/package.json apps/worker-control/package-lock.json ./
RUN npm ci --omit=dev --no-audit --no-fund
COPY apps/worker-control/*.js ./

FROM python:3.12-slim-bookworm AS runtime

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    AMPERSAND_DATA_DIR=/data/ampersand \
    AMPERSAND_GCS_BUCKET=gen-lang-client-0564514768-ampersand-beta-media \
    AMPERSAND_MAX_DIRECT_UPLOAD_BYTES=1073741824 \
    AMPERSAND_STATIC_DIR=/app/dist \
    PORT=8080

RUN apt-get update \
    && apt-get install --yes --no-install-recommends ca-certificates ffmpeg fonts-dejavu-core libstdc++6 tini \
    && rm -rf /var/lib/apt/lists/*

COPY --from=control-builder /usr/local/bin/node /usr/local/bin/node

WORKDIR /app
COPY packages/contracts/python ./packages/contracts/python
COPY services/media-worker ./services/media-worker
RUN python -m pip install --no-cache-dir ./packages/contracts/python ./services/media-worker

COPY --from=web-builder /build/dist ./dist
COPY --from=control-builder /build/apps/worker-control ./apps/worker-control

RUN groupadd --gid 10001 ampersand \
    && useradd --uid 10001 --gid ampersand --no-create-home --home-dir /nonexistent \
        --shell /usr/sbin/nologin ampersand \
    && mkdir -p /data/ampersand \
    && chown -R ampersand:ampersand /app /data/ampersand

USER ampersand
EXPOSE 8080
VOLUME ["/data/ampersand"]
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["node", "/app/apps/worker-control/server.js"]
