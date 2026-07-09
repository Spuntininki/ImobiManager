#!/bin/bash
# =============================================================================
# ImobiManager Backend - Production Entrypoint
# Runs Alembic migrations and starts Gunicorn with Uvicorn workers.
# =============================================================================

set -e

echo "→ Running Alembic migrations..."
uv run alembic upgrade head
echo "✓ Migrations applied."

GUNICORN_WORKERS="${GUNICORN_WORKERS:-4}"
GUNICORN_PORT="${GUNICORN_PORT:-8000}"
GUNICORN_TIMEOUT="${GUNICORN_TIMEOUT:-120}"
GUNICORN_LOG_LEVEL="${GUNICORN_LOG_LEVEL:-info}"

echo "→ Starting Gunicorn (workers=${GUNICORN_WORKERS}, port=${GUNICORN_PORT})..."
exec uv run gunicorn \
  -k uvicorn.workers.UvicornWorker \
  -w "${GUNICORN_WORKERS}" \
  --bind "0.0.0.0:${GUNICORN_PORT}" \
  --timeout "${GUNICORN_TIMEOUT}" \
  --log-level "${GUNICORN_LOG_LEVEL}" \
  --access-logfile - \
  --error-logfile - \
  app.main:app
