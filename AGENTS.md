# ImobiManager

## Overview

ImobiManager is a real estate rental management system. The owner (landlord) logs in and can register properties (addresses), tenants, and rental contracts.

## Domain Model

The authoritative database schema lives in `backend/db/schema.dbml`.

- **User** — the logged-in account. One user can manage multiple owners.
- **Owner** (proprietário) — the legal or business entity that owns properties.
- **UserOwner** — links a user to the owners they are allowed to manage.
- **Property** (imóvel) — address owned by an owner; classified as HOUSE or COMMERCIAL.
- **Tenant** (inquilino) — person renting a property.
- **Contract** (contrato) — rental agreement between owner and tenant, including conditions and lifecycle status (PENDING, ACTIVE, EXPIRED, CANCELLED).
- **Documents** — RG/CPF/CNPJ records attached to owners and tenants.
- **ContractRentAdjustment** — history of rent adjustments applied to a contract.

## Tech Stack

- **Frontend**: React 19, Vite, Tailwind CSS v4, shadcn/ui, React Router.
- **Backend**: Python 3.14, FastAPI, Pydantic v2, SQLAlchemy 2.x (async), Alembic, PostgreSQL, UV.

## Conventions

- **Code language**: English.
- **UI language**: Brazilian Portuguese (pt-BR).
- **Default theme**: dark.
- **Development style**: incremental and iterative. Ask before committing or moving to the next major step.
- Keep changes minimal and focused.
- `backend/db/schema.dbml` is the source of truth for the data model.

## Folder Structure

- `frontend/` — React/Vite frontend application.
- `backend/` — FastAPI backend application.
  - `backend/db/schema.dbml` — PostgreSQL database schema in DBML format.
