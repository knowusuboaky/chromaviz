FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN useradd -m -u 1000 appuser && \
    apt-get update && apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ---- deps via requirements.txt ----
COPY requirements.txt /tmp/requirements.txt
ARG TORCH_CPU=false
RUN python -m pip install --upgrade pip && \
    if [ "$TORCH_CPU" = "true" ]; then \
      python -m pip install --no-cache-dir \
        --index-url https://download.pytorch.org/whl/cpu \
        torch torchvision torchaudio ; \
    fi && \
    python -m pip install --no-cache-dir -r /tmp/requirements.txt

# ---- app code ----
COPY . /app

# ---- env defaults (override with -e) ----
ENV FLASK_SERVER_ENDPOINT=http://0.0.0.0:5000 \
    PUBLIC_HOST=localhost \
    PUBLIC_PORT=5000 \
    CHROMA_MODE=persistent \
    CHROMA_DB_PATH=/app/chroma-data \
    EMBEDDINGS_MODE=local \
    EMBEDDING_MODEL=all-MiniLM-L6-v2 \
    EMBEDDING_MODEL_PATH=/app/models/all-MiniLM-L6-v2 \
    HF_HOME=/app/models \
    AUTO_OPEN_BROWSER=false \
    APP_FILE=app.py

RUN mkdir -p /app/chroma-data /app/models && chown -R appuser:appuser /app
USER appuser

# Expose ONLY Flask
EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --retries=5 \
  CMD curl -fsS http://127.0.0.1:5000/heartbeat || exit 1

CMD ["sh", "-lc", "python ${APP_FILE}"]
