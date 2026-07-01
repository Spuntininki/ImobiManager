# ImobiManager

## Overview

ImobiManager is a real estate rental management system. The owner (landlord) logs in and can register properties (addresses), tenants, and rental contracts.

## Domain Model

- **Owner** (proprietário) — the logged-in user.
- **Property** (imóvel) — address owned by the landlord.
- **Tenant** (inquilino) — person renting a property.
- **Contract** (contrato) — rental agreement between owner and tenant.

## Tech Stack

- React 19
- Vite
- Tailwind CSS v4
- shadcn/ui
- React Router

## Conventions

- **Code language**: English.
- **UI language**: Brazilian Portuguese (pt-BR).
- **Default theme**: dark.
- **Development style**: incremental and iterative.
- Keep changes minimal and focused.

## Folder Structure

- `frontend/` — React/Vite frontend application.
  - `frontend/src/components/ui/` — shadcn/ui components.
  - `frontend/src/components/layout/` — layout components.
  - `frontend/src/pages/` — page components.
  - `frontend/src/lib/` — utility functions.
- `backend/` — FastAPI backend application (future).
  - `backend/db/schema.dbml` — PostgreSQL database schema in DBML format.
