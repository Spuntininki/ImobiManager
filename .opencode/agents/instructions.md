---
name: instructions
description: Default project agent for ImobiManager. Use for every task in this repository to enforce conventions and business context.
mode: primary
---

# ImobiManager - Project Instructions

## Overview

ImobiManager is a real estate rental management system. The owner (landlord) logs in and can register properties (addresses), tenants, and rental contracts.

## Domain Model

The authoritative database schema lives in `backend/db/schema.dbml`. Concept mapping:

- **User** — the logged-in account. One user can manage multiple owners.
- **Owner** (proprietário) — the legal or business entity that owns properties.
- **UserOwner** — links a user to the owners they are allowed to manage.
- **Property / Address** (imóvel) — address owned by an owner; classified as HOUSE or COMMERCIAL.
- **Tenant** (inquilino) — person renting a property.
- **Contract** (contrato) — rental agreement between owner and tenant, including conditions and lifecycle status (PENDING, ACTIVE, EXPIRED, CANCELLED).
- **Documents** — RG/CPF/CNPJ records attached to owners and tenants.
- **ContractRentAdjustment** — history of rent adjustments applied to a contract.

## Tech Stack

- **Frontend**: React 19, Vite, Tailwind CSS v4, shadcn/ui, React Router.
- **Backend**: Python 3.14, FastAPI, Pydantic v2, SQLAlchemy 2.x (async), Alembic, PostgreSQL, UV.

## Conventions

- **Code language**: English (file names, components, functions, variables, routes, constants, API messages).
- **UI language**: Brazilian Portuguese (pt-BR).
- **Default theme**: dark.
- **Development style**: incremental and iterative. Ask before committing or moving to the next major step. Ask for clarification when requirements are ambiguous.
- **Changes**: keep them minimal and focused on the requested task.
- **Database**: `backend/db/schema.dbml` is the source of truth for the data model.

## Folder Structure

- `frontend/` — React/Vite frontend application.
- `backend/` — FastAPI backend application.
  - `backend/db/schema.dbml` — PostgreSQL database schema in DBML format (authoritative).

Stack-specific conventions and folder layouts are defined in the dedicated skills:

- **Frontend skill** — load when working under `frontend/`.
- **Backend skill** — load when working under `backend/`.

## Routes

- `/` — Dashboard
- `/properties` — Properties (Imóveis)
- `/tenants` — Tenants (Inquilinos)
- `/contracts` — Contracts (Contratos)
