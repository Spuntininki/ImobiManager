# ImobiManager

Real estate rental management system. Monorepo with a React/Vite frontend and a FastAPI backend, backed by PostgreSQL.
Currently under active development, with the core property, tenant, and contract management flows already implemented in both frontend and backend.

## Architecture

```
ImobiManager/
├── docker-compose.yml  Project-level orchestrator (Postgres, backend, frontend, bot)
├── .env                Docker Compose shared environment variables
├── backend/
│   ├── .env            Local bare-metal development environment
│   ├── Dockerfile      Multi-stage backend image (dev/prod)
│   ├── entrypoint.sh   Runs Alembic migrations + starts Uvicorn
│   ├── .dockerignore
│   └── db/
│       ├── schema.dbml  Authoritative PostgreSQL schema (DBML)
│       └── init.sql     PostgreSQL init script (creates test DB)
├── bot/
│   ├── .env             Bot-only environment (Telegram, OpenRouter, backend URL)
│   ├── Dockerfile       Multi-stage bot image (dev/prod)
│   └── .dockerignore
├── frontend/
│   ├── Dockerfile       Multi-stage frontend image (dev/build/prod)
│   ├── nginx.conf       Nginx config for production stage
│   └── .dockerignore
```

`docker-compose.yml` lives at the repo root as the project-level orchestrator. It runs Postgres, backend (FastAPI + Uvicorn), frontend (Vite Dev Server or Nginx depending on target), and the Telegram bot (long-polling, no exposed ports).

## Prerequisites

- Docker and Docker Compose (recommended for full environment)
- Node.js 22+ and [UV](https://docs.astral.sh/uv/) (if running without Docker)

## Quickstart

### One command setup (Docker Compose — recommended)

```bash
docker compose up --build -d
```

Starts Postgres, backend (with automatic Alembic migrations), the Telegram bot (long-polling), and frontend (Vite Dev Server with HMR):

| Service  | URL                         |
|----------|-----------------------------|
| Frontend | http://localhost:5174       |
| Backend  | http://localhost:8000       |
| Health   | `GET http://localhost:8000/health` → `{"status":"ok"}` |
| Bot      | No URL — polls Telegram outbound, no exposed port |

To rebuild after changing `Dockerfile`, `pyproject.toml` or `package.json`:
```bash
docker compose up --build -d
```

To view logs:
```bash
docker compose logs -f
```

To stop:
```bash
docker compose down
```

### Setup without Docker (alternative)

If you prefer running locally without containerizing the backend and frontend:

> The root `.env` in the project root is used by Docker Compose (with `postgres`
> as the database host). The `backend/.env` file copied below is for local
> development (with `localhost:5433`). Each reflects its own context.

#### 1. Database

```bash
docker compose up -d postgres
```

Starts Postgres 17 on host port `5433` and creates two databases: `imobimanager` (dev) and `imobimanager_test` (tests).

#### 2. Backend

```bash
cp backend/.env.example backend/.env   # then edit values if needed
cd backend
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

API at http://localhost:8000.

#### 2b. Create the first admin user (CLI)

```bash
cd backend
uv run python -m app.cli create-user --email admin@imobi.com --name Admin
# Password will be prompted securely (hidden, with confirmation).
```

Operator CLI also provides `delete-user` and `update-password`:

```bash
uv run python -m app.cli delete-user --email admin@imobi.com          # prompts to confirm
uv run python -m app.cli delete-user --email admin@imobi.com --yes    # skip confirmation
uv run python -m app.cli update-password --email admin@imobi.com      # prompts for new password
```

#### 3. Frontend

```bash
cd frontend
npm ci        # deterministic install (respects package-lock.json)
npm run dev
```

SPA at http://localhost:5173. In dev, Vite proxies `/api` → `http://localhost:8000`
(see `vite.config.js`), so start the backend first. `npm install` is only for
adding/upgrading dependencies (it updates the lock file); use `npm ci` for
fresh clones and CI.

#### 4. Telegram Bot

```bash
cp bot/.env.example bot/.env   # then fill in TELEGRAM_BOT_TOKEN, OPENROUTER_API_KEY, BOT_MCP_API_KEY
cd bot
uv sync
uv run python -m app.main
```

Prerequisites: a Telegram bot token from [@BotFather](https://t.me/BotFather) and an OpenRouter API key from [openrouter.ai](https://openrouter.ai/keys). `BOT_MCP_API_KEY` must match the backend's value.

To issue a bot token (so a user can talk to the bot):

```bash
cd backend
# 1. Login as an existing user
RESP=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@imobi.com","password":"<your-password>"}')
TOK=$(echo "$RESP" | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

# 2. Create a bot token (USER type — returns the plain token ONCE)
curl -s -X POST http://localhost:8000/api/v1/bot-tokens \
  -H "Authorization: Bearer $TOK" \
  -H 'Content-Type: application/json' \
  -d '{"subject_type":"USER"}'
```

In Telegram, send `/start <TOKEN>` to the bot. After that, send questions normally
(ex.: "quantos imóveis eu tenho?"). See `bot/README.md` for details.

## Testing

```bash
# Inside the container (recommended — uses the Docker environment)
docker compose exec backend uv run pytest
docker compose exec bot uv run pytest

# Or locally (with Python installed and postgres running)
cd backend
uv run pytest

# Bot tests are in-memory (no DB needed)
cd bot
uv run pytest
```

Backend tests run against the `imobimanager_test` database, so Postgres must be up. Bot tests are self-contained.

## Lint and Format

```bash
cd backend
uv run ruff check .
uv run ruff format .          # apply formatting

cd bot
uv run ruff check .
uv run ruff format .
```

## Production build

```bash
BACKEND_TARGET=prod FRONTEND_TARGET=prod BOT_TARGET=prod docker compose up --build -d
```

- Frontend served by Nginx on port 80.
- Backend runs with **Gunicorn + Uvicorn workers** (instead of plain Uvicorn), providing worker management, graceful shutdown, and automatic restarts.
- Bot runs `uv run python -m app.main` (asyncio loop, no HTTP server, no exposed ports).
- Set `CORS_ORIGINS` and `SECRET_KEY` in `.env` appropriately for production.
- Optional: configure `GUNICORN_WORKERS` (default 4), `GUNICORN_TIMEOUT` (default 120s) and `GUNICORN_LOG_LEVEL` (default info) via environment variables.

## Project Layout

### Backend

- `backend/app/main.py` — FastAPI application entrypoint.
- `backend/app/api/v1/endpoints/` — route handlers (HTTP only).
- `backend/app/core/` — configuration, security, logging.
- `backend/app/db/` — SQLAlchemy engine and session management.
- `backend/app/models/` — SQLAlchemy ORM models mirroring `schema/schema.dbml`.
- `backend/app/schemas/` — Pydantic models (request/response validation).
- `backend/app/services/` — business logic.
- `backend/app/tests/` — test suite.
- `backend/alembic/` — database migrations.
- `backend/schema/schema.dbml` — authoritative PostgreSQL schema (DBML reference, not runtime code).

### Frontend

- `frontend/src/components/ui/` — shadcn/ui components.
- `frontend/src/components/layout/` — layout components.
- `frontend/src/pages/` — page components mapped to routes.
- `frontend/src/lib/` — utility functions.

### Bot

- `bot/app/main.py` — entrypoint (Telegram polling loop).
- `bot/app/platforms/telegram/` — Telegram `getUpdates` long-polling client.
- `bot/app/security/` — token auth (HTTP client + cache) and 3-layer rate limiter.
- `bot/app/llm/` — LangChain agent, MCP client, tools, chat history.
- `bot/app/prompts/` — system prompt, role-specific prompts (USER/RENTER), guardrails.
- `bot/app/router.py` — message dispatch (commands, sessions, agent invocation).
- See `bot/README.md` for the full architecture and documented technical debt.

## Routes (frontend)

- `/` — Dashboard
- `/properties` — Properties (Imóveis)
- `/tenants` — Tenants (Inquilinos)
- `/contracts` — Contracts (Contratos)

## API endpoints (backend)

All under `/api/v1`, require `Authorization: Bearer <jwt>` unless noted.

- `POST /auth/login` — exchange email + password for a JWT (no auth required).
- `/owners` — CRUD; scoped to the caller via `user_owners` (404-only, no 403 leakage).
- `POST /owners/{owner_id}/renters` — create a renter under an owner (scoped).
- `GET  /owners/{owner_id}/renters` — list renters for an owner (scoped).
- `/renters/{renter_id}` — GET / PUT / DELETE; scoped via `owner_renters` (404-only).
- `/renters/{renter_id}/documents` — POST / GET list; one document per type per renter (unique constraint). Reads are **masked** (last 2 digits for CPF/CNPJ, last 1 for RG) — the raw value never crosses HTTP.
- `GET/PUT/DELETE /renters/{renter_id}/documents/{document_id}` — 404 if the document belongs to a different renter; 409 on duplicate type via PUT.
- `POST /owners/{owner_id}/addresses` — create a property address under an owner (scoped).
- `GET  /owners/{owner_id}/addresses` — list addresses for an owner (scoped).
- `/addresses/{address_id}` — GET / PUT / DELETE; scoped via the owner on the address (404-only). `type` is `HOUSE` or `COMMERCIAL`.
- `/owners/{owner_id}/documents` — POST / GET list; one document per type per owner (unique constraint). Reads are **masked** (last 2 digits for CPF/CNPJ, last 1 for RG) — the raw value never crosses HTTP.
- `GET/PUT/DELETE /owners/{owner_id}/documents/{document_id}` — 404 if the document belongs to a different owner; 403 on duplicate type via PUT.
- `POST /owners/{owner_id}/contracts` — create a contract tying together an owner, a renter, and an address. `status` auto-`PENDING`, `generation_date` auto-`now()`. Validates renter↔owner (via `owner_renters`) and address↔owner consistency — 422 on mismatch. `*_file_path` fields are not accepted from clients (backend-only).
- `GET  /owners/{owner_id}/contracts` — list contracts for an owner (scoped).
- `/contracts/{contract_id}` — GET / PATCH (partial) / DELETE; scoped via the contract's owner (404-only). PATCH accepts status/lifecycle changes (free transitions); `*_file_path` not accepted. Money fields use `Numeric(12, 2)`.

Migrations: `cd backend && uv run alembic upgrade head`.
Admin user: `cd backend && uv run python -m app.cli create-user ...` (see step 2b above).

### Chat bot endpoints

- `POST /api/v1/bot-tokens` (admin, JWT-auth) — issue a bot token (USER or RENTER). Returns the plain token ONCE.
- `GET /api/v1/bot-tokens` (admin, JWT-auth) — list tokens (redacted).
- `POST /api/v1/bot-tokens/{id}/revoke` (admin, JWT-auth) — revoke a token.
- `POST /api/v1/bot/auth/validate` (machine-to-machine, `X-Bot-Api-Key`) — validate a token + bind `chat_id`.
- `POST /api/v1/bot/message-logs` (machine-to-machine, `X-Bot-Api-Key`) — batch audit log.
- `POST /mcp` — MCP server (Streamable HTTP) with read-only, role-aware tools scoped by `X-Bot-Subject-Type` + `X-Bot-Subject-Id` headers.