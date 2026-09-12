# ==============================================================================
# Production Dockerfile for Pan-India Educational Institutions Dashboard
# Multi-stage optimized build using Python 3.11-slim
# ==============================================================================

FROM python:3.11-slim AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install build tools if necessary for native extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ------------------------------------------------------------------------------
# Production Runtime Stage
# ------------------------------------------------------------------------------
FROM python:3.11-slim AS runner

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/home/appuser/.local/bin:$PATH \
    PORT=8000 \
    HOST=0.0.0.0 \
    ENV=production

# Create non-root user for security compliance
RUN groupadd -g 1001 appgroup && \
    useradd -u 1001 -g appgroup -m -s /bin/bash appuser

# Copy installed wheels from builder
COPY --from=builder --chown=appuser:appgroup /root/.local /home/appuser/.local

# Copy application codebase
COPY --chown=appuser:appgroup . .

# Ensure source data is read-only for security
RUN chmod -R 755 /app && \
    chmod -R 555 /app/data/raw 2>/dev/null || true

USER appuser

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + str(os.environ.get('PORT', 8000)) + '/api/summary')" || exit 1

# Production server start: Gunicorn with Uvicorn workers
CMD ["sh", "-c", "gunicorn dashboard_server:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind ${HOST}:${PORT} --access-logfile - --error-logfile -"]
