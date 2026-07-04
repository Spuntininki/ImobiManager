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

Migrations: `cd backend && uv run alembic upgrade head`.
Admin user: `cd backend && uv run python -m app.cli create-user ...` (see step 2b above).
<!-- TODO future: Frontend Docker image added to docker-compose.yml -->