---
name: instructions
description: Default project agent for ImobiManager. Use for every task in this repository to enforce conventions and business context.
mode: primary
---

# ImobiManager - Project Instructions

## Overview

ImobiManager is a real estate rental management system. The owner (landlord) logs in and can register properties (addresses), tenants, and rental contracts.

## Domain Model

- **Owner** (proprietário) — the logged-in user who owns the properties.
- **Property** (imóvel) — address owned by the landlord.
- **Tenant** (inquilino) — person renting a property.
- **Contract** (contrato) — rental agreement between owner and tenant, including conditions.

## Tech Stack

- React 19
- Vite
- Tailwind CSS v4
- shadcn/ui
- React Router

## Conventions

- **Code language**: English (file names, components, functions, variables, routes, constants).
- **UI language**: Brazilian Portuguese (pt-BR).
- **Default theme**: dark.
- **Development style**: incremental and iterative. Ask before committing or moving to the next major step.
- **Changes**: keep them minimal and focused on the requested task.

## Folder Structure

- `src/components/ui/` — shadcn/ui components.
- `src/components/layout/` — layout components (Navbar, Sidebar, etc.).
- `src/pages/` — page components mapped to routes.
- `src/lib/` — utility functions (e.g., `cn` helper).

## Routes

- `/` — Dashboard
- `/properties` — Properties (Imóveis)
- `/tenants` — Tenants (Inquilinos)
- `/contracts` — Contracts (Contratos)
