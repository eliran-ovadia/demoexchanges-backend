FROM python:3.14-slim

WORKDIR /app

# Install dependencies first (layer cache-friendly)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Non-root user for security
RUN adduser --disabled-password --gecos "" appuser
USER appuser

EXPOSE 8000

# 2 * vCPU + 1 workers — tune via ECS task definition env var GUNICORN_WORKERS
CMD ["sh", "-c", "gunicorn src.exchange.main:app \
    -w ${GUNICORN_WORKERS:-3} \
    -k uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -"]
