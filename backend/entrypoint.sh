#!/bin/bash
# =============================================================================
# ImobiManager Backend - Entrypoint
# Runs Alembic migrations and starts Uvicorn.
# Supports hot-reload in dev via UVICORN_RELOAD env var.
# =============================================================================

set -e

echo "→ Running Alembic migrations..."
uv run alembic upgrade head
echo "✓ Migrations applied."

if [ "${UVICORN_RELOAD:-true}" = "true" ]; then
  echo "→ Starting Uvicorn with hot-reload..."
  exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
else
  echo "→ Starting Uvicorn..."
  exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
fi