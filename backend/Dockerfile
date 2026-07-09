# =============================================================================
# ImobiManager Backend - Dockerfile
# Multi-stage: dev (default) | prod
# =============================================================================

# ---- Base stage ----
FROM python:3.14-slim AS base

# Install UV (fast Python package manager)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV \
  PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1 \
  UV_COMPILE_BYTECODE=1 \
  UV_LINK_MODE=copy

WORKDIR /app

# ---- Dev stage ----
FROM base AS dev

COPY pyproject.toml uv.lock /app/

# Install all dependencies (including dev)
RUN uv sync --frozen --no-cache

COPY . .

EXPOSE 8000

RUN chmod +x entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]

# ---- Prod stage ----
FROM base AS prod

COPY pyproject.toml uv.lock /app/

# Install only production dependencies
RUN uv sync --frozen --no-cache --no-dev

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]