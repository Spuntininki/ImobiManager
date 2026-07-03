---
name: frontend
description: Use when working on the React/Vite frontend — files under `frontend/`, React components, pages, routes, shadcn/ui, Tailwind, or Vite config. Enforces frontend conventions and folder structure.
---

# ImobiManager - Frontend

## Overview

React/Vite single-page application for ImobiManager. Consumes the FastAPI backend API.

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
- **Dependencies**: before adding or updating any package, check its latest version from npm in the command line (e.g. `npm view <package> version`). Use a caret range (`^x.y.z`) or pin as appropriate, and let `package-lock.json` lock exact patches. Never guess versions.
- **Commit messages**: concise. One imperative subject line (`feat: add owner CRUD`, `fix: reject negative rent`) in conventional-commits style; add a short body only when context is genuinely needed. Avoid multi-line summaries.
- **Development style**: incremental and iterative. Ask before committing or moving to the next major step. Ask for clarification when requirements are ambiguous.
- **Changes**: keep them minimal and focused on the requested task.

## Folder Structure

- `frontend/src/components/ui/` — shadcn/ui components.
- `frontend/src/components/layout/` — layout components (Navbar, Sidebar, etc.).
- `frontend/src/pages/` — page components mapped to routes.
- `frontend/src/lib/` — utility functions (e.g., `cn` helper).

## Routes

- `/` — Dashboard
- `/properties` — Properties (Imóveis)
- `/tenants` — Tenants (Inquilinos)
- `/contracts` — Contracts (Contratos)
