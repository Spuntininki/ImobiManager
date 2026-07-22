# ImobiManager

## Overview

ImobiManager is a real estate rental management system. The owner (landlord) logs in and can register properties (addresses), tenants, and rental contracts.

## Domain Model

The authoritative database schema lives in `backend/schema/schema.dbml`.

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
- **Bot**: Python 3.14, asyncio, httpx, LangChain 1.x (create_agent + tools), MCP client (streamable HTTP), OpenRouter (OpenAI-compatible), UV.

## Conventions

- **Code language**: English.
- **UI language**: Brazilian Portuguese (pt-BR).
- **Default theme**: dark.
- **Development style**: incremental and iterative. Ask before committing or moving to the next major step.
- Keep changes minimal and focused.
- `backend/schema/schema.dbml` is the source of truth for the data model.
- **Migrations** (Alembic): forward-only — maintain `upgrade()` only, do not rely on `downgrade()`.

## Folder Structure

- `frontend/` — React/Vite frontend application.
- `backend/` — FastAPI backend application.
  - `backend/schema/schema.dbml` — PostgreSQL database schema in DBML format.
- `bot/` — Telegram bot application (separate pod, HTTP-only, never touches the DB).
  - `bot/app/platforms/telegram/` — Telegram long-polling client.
  - `bot/app/security/` — token auth (HTTP client + cache) and rate limiting.
  - `bot/app/llm/` — LangChain agent, MCP client, tools, chat history.
  - `bot/app/prompts/` — system prompt, role-specific prompts, guardrails.

## Chat Bot Architecture

The bot is a top-level service (`bot/`) deployed as a separate pod. It polls Telegram via `getUpdates` (outbound-only, no exposed ports) and forwards authenticated chat messages to a LangChain agent whose tools call the backend's MCP server over HTTP.

**Key principle**: the bot never connects to the database. All communication with the backend is via HTTP:
- `POST /api/v1/bot/auth/validate` — validates a short token and binds `chat_id` on first contact.
- `POST /api/v1/bot/message-logs` — batch audit log (fire-and-forget).
- `POST /mcp` — MCP server (Streamable HTTP) with read-only, role-aware tools scoped by `X-Bot-Subject-Type` + `X-Bot-Subject-Id` headers.

The backend exposes:
- `POST /api/v1/bot-tokens` (admin, JWT-auth) — issues tokens (USER or RENTER, polymorphic via `subject_type + subject_id`).
- `POST /api/v1/bot-tokens/{id}/revoke` — revokes a token.
- `POST /bot/auth/validate` + `POST /bot/message-logs` — machine-to-machine endpoints (shared `BOT_MCP_API_KEY`).
- `POST /mcp` — MCP server with read-only tools: `list_owners`, `list_addresses`, `list_active_contracts`, `get_renter`.

LangChain usage is restricted to `bot/app/llm/` (agent + tools + memory + prompts). The default LLM model is `google/gemma-4-31b-it:free` via OpenRouter.

### Token auth flow
1. Admin issues a token via `POST /api/v1/bot-tokens` (returns the plain token once).
2. User sends `/start <TOKEN>` in Telegram.
3. Bot validates via `POST /bot/auth/validate`; backend binds `chat_id` to the token on first contact.
4. Bot stores `chat_id → token` in `ChatSessionStore` (in-memory); follow-up messages need no token prefix.
5. Commands: `/start`, `/help`, `/logout`.

### Rate limiting (hard reject, in-memory, single-pod)
- **Per token**: rolling minute + sliding day counter; limits differ by subject type (USER vs RENTER).
- **Per chat**: rolling minute window (protects against token reuse from the same chat).
- **Per-token lock**: one message processed at a time per client; duplicates are silently dropped.
- throttle replies are gated to at most one per 30s per chat.

### Documented technical debt
- **Single-pod only**: rate-limit windows and `ChatSessionStore` are per-pod; scaling to multiple replicas needs a shared store (Redis) or sticky routing.
- **No health probe**: the bot has no HTTP server; k8s restarts on process death.
- **No Service/Ingress**: purely outbound (polls Telegram, calls backend).
- **Cache TTL**: token validation results cached ~60s in the bot pod; revocation takes up to that long to propagate (restart for immediate effect).
- **Chat history in memory**: lost on pod restart; user re-runs `/start`.
- **No backpressure**: LLM is invoked sequentially per token (one in-flight per client); a global concurrency limit / queue is deferred.
