# ---- base image ----
FROM python:3.11-slim

# System deps: nginx + supervisor + build basics
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx supervisor build-essential curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Clean default nginx sites to avoid conflicts
RUN rm -f /etc/nginx/sites-enabled/default /etc/nginx/conf.d/default.conf || true

# App layout
WORKDIR /app

# ----- Python deps (cached) -----
# Copy requirements first to maximize Docker layer caching
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r /tmp/requirements.txt

# Copy your app (must include static/ and chromaviz/ assets)
COPY . /app

# Nginx + Supervisor configs
COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf
COPY deploy/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Runtime dirs
RUN mkdir -p /data /app/models /run/nginx

# Defaults (overridable via env or docker-compose)
ENV CHROMA_SERVER_HOST=0.0.0.0 \
    CHROMA_SERVER_HTTP_PORT=8000 \
    CHROMA_DATA_PATH=/data \
    ANONYMIZED_TELEMETRY=False \
    # ---- UI/env defaults ----
    FLASK_SERVER_ENDPOINT=http://0.0.0.0:5000 \
    PUBLIC_HOST=localhost \
    PUBLIC_PORT=8000 \
    CHROMA_MODE=http \
    CHROMA_HTTP_HOST=127.0.0.1 \
    CHROMA_HTTP_PORT=8000 \
    EMBEDDING_MODEL=all-MiniLM-L6-v2 \
    EMBEDDING_MODEL_PATH=/app/models/all-MiniLM-L6-v2 \
    CONTINUE_WITHOUT_EMBEDDINGS=true \
    AUTO_OPEN_BROWSER=false \
    GUNICORN_WORKERS=2 \
    UI_MODULE=app:app

# Nginx listens on 80 in the container
EXPOSE 80

# Healthcheck hits your Flask heartbeat via Nginx prefix
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
  CMD curl -fsS http://127.0.0.1/dashboard/heartbeat || exit 1

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
