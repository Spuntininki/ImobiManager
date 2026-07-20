# =============================================================================
# ImobiManager Bot - Dockerfile
# Multi-stage: dev (default) | prod
# =============================================================================

FROM python:3.14-slim AS base

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV \
  PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1 \
  UV_COMPILE_BYTECODE=1 \
  UV_LINK_MODE=copy

WORKDIR /app

# ---- Dev stage ----
FROM base AS dev
COPY pyproject.toml uv.lock* /app/
RUN uv sync --no-cache
COPY . .
CMD ["uv", "run", "python", "-m", "app.main"]

# ---- Prod stage ----
FROM base AS prod
COPY pyproject.toml uv.lock* /app/
RUN uv sync --no-cache --no-dev
COPY . .
CMD ["uv", "run", "python", "-m", "app.main"]