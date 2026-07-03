---
name: backend
description: Use when working on the FastAPI backend — Python under `backend/app`, API endpoints, SQLAlchemy models, Pydantic schemas, Alembic migrations, or UV package management. Enforces backend conventions, folder structure, and the domain model from `backend/db/schema.dbml`.
---

# ImobiManager - Backend

## Overview

FastAPI REST backend for ImobiManager. Exposes the API consumed by the React frontend.

## Tech Stack

- Python 3.14
- FastAPI
- Pydantic v2 (validation) + pydantic-settings (`.env` config)
- SQLAlchemy 2.x (async)
- Alembic (migrations)
- PostgreSQL
- Ruff (lint + format)
- UV (package manager)

## Conventions

- **Code language**: English (file names, modules, functions, variables, routes, constants, API response/error messages, logs).
- **Architecture**: layered — thin API endpoints → services (business logic) → models (ORM) + schemas (I/O validation).
- **Async**: use `async`/`await` and async SQLAlchemy sessions throughout.
- **Database**: `backend/db/schema.dbml` is the source of truth for the data model. Models must mirror it.
- **Dependencies**: before adding or pinning any package, check its latest version from PyPI in the command line (e.g. `curl -s https://pypi.org/pypi/<package>/json | python3 -c "import sys,json; print(json.load(sys.stdin)['info']['version'])"`). Pin to the current major (e.g. `>=0.139,<0.140`) and let UV lock exact patches in `uv.lock`. Never guess versions.
- **Development style**: incremental and iterative. Ask before committing or moving to the next major step. Ask for clarification when requirements are ambiguous.
- **Changes**: keep them minimal and focused on the requested task.

## Domain Model

Authoritative schema: `backend/db/schema.dbml`. Table/concept mapping:

- `users` — login account. One user can manage multiple owners.
- `owners` — legal or business name of the property owner.
- `user_owners` — links a user to the owners they may manage.
- `owner_documents` — RG/CPF/CNPJ records for an owner.
- `renters` — tenant; includes contacts and email.
- `renter_documents` — RG/CPF/CNPJ records for a tenant.
- `addresses` — property (HOUSE or COMMERCIAL) owned by an owner.
- `contracts` — rental agreement (owner + renter + address) with status, dates, rent, deposit, and contract file paths.
- `contract_rent_adjustments` — history of rent adjustments per contract.

Enums:

- `document_types` — RG, CPF, CNPJ.
- `property_type` — HOUSE, COMMERCIAL.
- `contract_status` — PENDING, ACTIVE, EXPIRED, CANCELLED.

## Folder Structure

- `backend/app/` — FastAPI application.
  - `backend/app/main.py` — application entrypoint.
  - `backend/app/api/v1/endpoints/` — route handlers (HTTP only).
  - `backend/app/core/` — configuration, security, logging.
  - `backend/app/db/` — SQLAlchemy engine and session management.
  - `backend/app/models/` — SQLAlchemy ORM models.
  - `backend/app/schemas/` — Pydantic models (request/response validation).
  - `backend/app/services/` — business logic.
  - `backend/app/tests/` — test suite.
- `backend/alembic/` — database migrations.
- `backend/db/schema.dbml` — PostgreSQL schema in DBML (authoritative reference; not runtime code).
- `backend/pyproject.toml` — UV project config.
- `backend/.env` — environment variables.

## Layering Rules

- `api/v1/endpoints/` — HTTP concerns only: parse request, call a service, return a schema. No business logic here.
- `services/` — all business logic. Orchestrates models and schemas; the only place that enforces rules.
- `models/` — SQLAlchemy ORM definitions mirroring `schema.dbml`.
- `schemas/` — Pydantic models for request/response validation and serialization.
- `core/` — cross-cutting concerns (settings, security, logging).
- `db/` — engine/session setup consumed by services and endpoints.
