# ImobiManager

Real estate rental management system. Monorepo with a React/Vite frontend and a FastAPI backend, backed by PostgreSQL.

## Architecture

```
ImobiManager/
├── frontend/          React 19 + Vite SPA (UI in pt-BR)
├── backend/           FastAPI app, SQLAlchemy, Alembic, UV
│   └── db/schema.dbml  Authoritative PostgreSQL schema (DBML)
├── docker-compose.yml Project-level orchestrator (Postgres today,
│                      frontend/backend images planned later)
└── docker/            Container artifacts (init scripts, Dockerfiles)
    └── postgres/
```

`docker-compose.yml` lives at the repo root as the project-level orchestrator. Today it runs Postgres only; future frontend and backend Docker images will join it.

## Prerequisites

- Node.js (for the frontend)
- Python 3.14 and [UV](https://docs.astral.sh/uv/) (for the backend)
- Docker and Docker Compose (for Postgres)

## Quickstart

### 1. Database (shared)

```bash
docker compose up -d
```

Starts Postgres 17 on host port `5433` and creates two databases: `imobimanager` (dev) and `imobimanager_test` (tests).

### 2. Backend

```bash
cp backend/.env.example backend/.env   # then edit values if needed
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

API at http://localhost:8000. Health check: `GET /health` → `{"status":"ok"}`.

### 2b. Create the first admin user (CLI)

```bash
cd backend
uv run python -m app.cli create-user --email admin@imobi.com --name Admin
# Password will be prompted securely (hidden, with confirmation).
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

SPA at http://localhost:5173.

## Testing

```bash
cd backend
uv run pytest
```

Tests run against the `imobimanager_test` database, so Postgres must be up (`docker compose up -d`).

## Lint and Format

```bash
cd backend
uv run ruff check .
uv run ruff format .          # apply formatting
```

## Project Layout

### Backend

- `backend/app/main.py` — FastAPI application entrypoint.
- `backend/app/api/v1/endpoints/` — route handlers (HTTP only).
- `backend/app/core/` — configuration, security, logging.
- `backend/app/db/` — SQLAlchemy engine and session management.
- `backend/app/models/` — SQLAlchemy ORM models mirroring `db/schema.dbml`.
- `backend/app/schemas/` — Pydantic models (request/response validation).
- `backend/app/services/` — business logic.
- `backend/app/tests/` — test suite.
- `backend/alembic/` — database migrations.
- `backend/db/schema.dbml` — authoritative PostgreSQL schema (DBML reference, not runtime code).

### Frontend

- `frontend/src/components/ui/` — shadcn/ui components.
- `frontend/src/components/layout/` — layout components.
- `frontend/src/pages/` — page components mapped to routes.
- `frontend/src/lib/` — utility functions.

## Routes (frontend)

- `/` — Dashboard
- `/properties` — Properties (Imóveis)
- `/tenants` — Tenants (Inquilinos)
- `/contracts` — Contracts (Contratos)

<!-- TODO Phase 2: API endpoints documentation -->
<!-- TODO Phase 3: Auth documentation -->
<!-- TODO future: Frontend Docker image added to docker-compose.yml -->