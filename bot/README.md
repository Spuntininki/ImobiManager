# ImobiManager Bot

Telegram bot for ImobiManager. A single-pod, long-polling bot that forwards
authenticated chat messages to a LangChain agent whose tools call the
backend's MCP server over HTTP.

## What it does

- Polls Telegram via `getUpdates` (no webhook, no exposed port).
- Authenticates each chat with a short token issued by the backend admin
  API (`POST /api/v1/bot-tokens`); the first contact binds `chat_id` to the
  token via `POST /api/v1/bot/auth/validate`.
- Enforces in-memory hard-reject rate limits (per token, per chat, plus a
  per-token lock so only one message is processed at a time per client).
- Opens an MCP `ClientSession` per inbound LLM-bound message (subject headers
  baked into the HTTP transport so the LLM cannot forge the subject) and
  runs a LangChain `create_agent` graph built once at startup.
- Sends audit events (IN/OUT) to the backend in batches.

The bot **never** connects to the database. It never sees documents, JWTs,
passwords, or anything that isn't explicitly exposed by the backend.

## Local dev

```bash
# 1. Pick a Telegram bot: talk to @BotFather and copy the token.
# 2. Set up env
cp .env.example .env
# fill TELEGRAM_BOT_TOKEN, BOT_MCP_API_KEY (must match the backend), OPENROUTER_API_KEY
# 3. Run
uv sync
uv run python -m app.main
```

The backend must be running and reachable at `BOT_BACKEND_BASE_URL`. For
local dev fill it with `http://localhost:8000`; in docker-compose /
k8s it defaults to `http://backend:8000`.

## Chat conventions

- `/start <TOKEN>` — first-time link (binds chat_id to the token on the
  backend).
- `<TOKEN> <message>` — token precedes the message text.
- Messages without a token receive a generic onboarding hint (no LLM cost).

## Architecture notes (debt)

- **Single-pod only**: rate-limit windows are in-memory and per-pod. Scaling
  to N replicas needs a shared store (Redis) or sticky routing — out of
  scope for the MVP.
- **No backpressure**: the LLM is invoked sequentially per token (one
  in-flight per token). A global concurrency limit / queue is left for
  later.
- **Cache TTL**: token validation results are cached ~60s by default in the
  bot pod. Revoking a token takes up to that long to propagate. Restart the
  pod for immediate effect (documented limitation, see plan).
- **History store** is in-memory per chat_id with a small buffer; restarting
  the pod loses chat context (acceptable).

See `AGENTS.md` for the integration plan and `../backend/app/mcp/` for the
server-side counterparts.