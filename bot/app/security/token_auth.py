"""Token authentication for inbound messages.

The bot never reads the database. For every inbound message the router first
validates the token via `POST /api/v1/bot/auth/validate` on the backend,
sending the shared `BOT_MCP_API_KEY`. Validation results are cached for a
short TTL (default 60s) so a chatty user does not hammer the backend; a 401
invalidates the cache entry immediately.

Token parsing convention (kept simple for the MVP):
- `/start <TOKEN>` — first-time link. We POST validate; the backend binds
  chat_id on the first valid contact.
- `<TOKEN> <message>` (e.g. `ABC123 quando vence meu aluguel?`) — token
  precedes the rest of the message.
- Messages without a token receive a generic onboarding hint (no auth, no
  LLM cost).
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class AuthResult:
    """Outcome of validating a (token, chat_id) pair."""

    token_id: int
    subject_type: str
    subject_id: int
    status: str
    expires_at: str | None
    linked: bool


@dataclass(frozen=True, slots=True)
class ParsedCommand:
    """What `parse_message` extracted from the inbound text."""

    token: str | None
    body: str


class ChatSessionStore:
    """In-memory mapping of `chat_id` to the validated token for that chat.

    After `/start <TOKEN>` succeeds, the bot stores the token here so the
    user can send follow-up questions without re-prefixing the token every
    time. On revoke/expiry (validate returns None), the router clears the
    entry so the chat falls back to onboarding.

    Limitations (documented debt):
    - Per-pod only; multi-replica deployments need a shared store (Redis).
    - Lost on pod restart; the user re-runs `/start`.
    """

    __slots__ = ("_sessions",)

    def __init__(self) -> None:
        self._sessions: dict[int, str] = {}

    def get(self, chat_id: int) -> str | None:
        return self._sessions.get(chat_id)

    def set(self, chat_id: int, token: str) -> None:
        self._sessions[chat_id] = token

    def clear(self, chat_id: int) -> None:
        self._sessions.pop(chat_id, None)


def parse_message(text: str) -> ParsedCommand:
    """Split the inbound text into an optional token and the message body.

    Returns `token=None` when nothing looking like a token was found, in
    which case the router will answer with the generic onboarding hint.
    """
    stripped = text.strip()
    if not stripped:
        return ParsedCommand(token=None, body="")
    # /start <TOKEN>
    if stripped.startswith("/start"):
        parts = stripped.split(maxsplit=1)
        if len(parts) < 2 or not parts[1].strip():
            return ParsedCommand(token=None, body="")
        token = parts[1].split(maxsplit=1)[0].strip()
        rest = parts[1][len(token) :].strip()
        return ParsedCommand(token=token or None, body=rest)
    # <TOKEN> <rest...> — at least one whitespace-separated token + body.
    parts = stripped.split(maxsplit=1)
    if len(parts) == 1:
        # Bare token-like word with no body — still treat as a `ping`.
        return ParsedCommand(token=parts[0], body="")
    token, body = parts[0], parts[1]
    return ParsedCommand(token=token, body=body)


class TokenAuthenticator:
    """HTTP client + tiny TTL cache for `POST /bot/auth/validate`."""

    def __init__(self, http: httpx.AsyncClient) -> None:
        self._http = http
        self._cache: dict[str, tuple[float, AuthResult]] = {}

    def _cached(self, token: str) -> AuthResult | None:
        entry = self._cache.get(token)
        if entry is None:
            return None
        expires_at, result = entry
        if time.monotonic() > expires_at:
            self._cache.pop(token, None)
            return None
        return result

    def _set_cached(self, token: str, result: AuthResult) -> None:
        self._cache[token] = (time.monotonic() + settings.bot_validate_cache_ttl, result)

    def invalidate(self, token: str) -> None:
        """Drop a cache entry (call after a 401 on subsequent MCP calls)."""
        self._cache.pop(token, None)

    async def validate(self, token: str, chat_id: int) -> AuthResult | None:
        """Validate a token against the backend and cache the short-lived result.

        Returns `None` on any failure (404 unknown token, REVOKED, expired,
        wrong chat, network error). The router treats `None` as "ignore"
        rather than replying, to avoid giving attackers acknowledgment of
        valid vs invalid tokens.
        """
        cached = self._cached(token)
        if cached is not None:
            return cached
        url = f"{settings.bot_backend_base_url}/api/v1/bot/auth/validate"
        try:
            resp = await self._http.post(
                url,
                json={"token": token, "chat_id": chat_id},
                headers={"X-Bot-Api-Key": settings.bot_mcp_api_key},
            )
        except httpx.HTTPError as exc:
            logger.warning("validate HTTP error: %s", exc)
            return None
        if resp.status_code != 200:
            return None
        body = resp.json()
        result = AuthResult(
            token_id=body["token_id"],
            subject_type=body["subject_type"],
            subject_id=body["subject_id"],
            status=body["status"],
            expires_at=body["expires_at"],
            linked=body["linked"],
        )
        self._set_cached(token, result)
        return result
