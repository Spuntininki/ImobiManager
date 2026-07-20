"""Telegram Bot API client (polling + sendMessage via httpx).

Keeps a single `httpx.AsyncClient` reused for the whole pod lifetime. The
`getUpdates` long-polling loop maintains the `offset` cursor: every call
passes `offset = last_update_id + 1` so the server discards already-processed
updates.

No outbound webhook, no exposed port — this is a polling-only client, which
matches the "pod ClusterIP-only" deployment decision.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

API_BASE = "https://api.telegram.org"


class TelegramError(RuntimeError):
    """Raised when the Telegram API returns a non-OK response."""


class TelegramClient:
    """Thin wrapper over the Telegram Bot API for polling and replying."""

    def __init__(self, http: httpx.AsyncClient | None = None) -> None:
        self._http = http or httpx.AsyncClient(timeout=httpx.Timeout(60.0))
        self._base = f"{API_BASE}/bot{settings.telegram_bot_token}"
        self._offset: int = 0

    async def aclose(self) -> None:
        await self._http.aclose()

    async def _post(self, method: str, **payload: Any) -> dict[str, Any]:
        resp = await self._http.post(f"{self._base}/{method}", json=payload)
        if resp.status_code != 200:
            raise TelegramError(f"{method} -> HTTP {resp.status_code}: {resp.text}")
        body = resp.json()
        if not body.get("ok"):
            raise TelegramError(f"{method} -> not ok: {body}")
        return body["result"]

    async def get_me(self) -> dict[str, Any]:
        """Return the bot identity (used to verify the token on startup)."""
        return await self._post("getMe")

    async def send_message(self, chat_id: int, text: str) -> None:
        """Send a plain text message to a chat.

        Telegram caps messages at 4096 chars; we split defensively to avoid
        hard failures from the LLM producing long answers.
        """
        for chunk in _chunk_text(text, 4000):
            await self._post("sendMessage", chat_id=chat_id, text=chunk)

    async def poll_updates(self) -> AsyncIterator[dict[str, Any]]:
        """Yield Telegram `update` objects forever via long polling.

        Loops until the consumer stops iterating (cancellation). On
        transient errors we sleep `telegram_polling_error_backoff` seconds
        and retry, so a bot restart is not required for a network blip.
        """
        while True:
            try:
                result = await self._post(
                    "getUpdates",
                    offset=self._offset,
                    timeout=settings.telegram_polling_timeout,
                    allowed_updates=["message"],
                )
            except (httpx.HTTPError, TelegramError) as exc:
                logger.warning("telegram getUpdates failed: %s", exc)
                await asyncio.sleep(settings.telegram_polling_error_backoff)
                continue
            for update in result:
                self._offset = int(update["update_id"]) + 1
                yield update


def _chunk_text(text: str, size: int) -> list[str]:
    """Split `text` into chunks of at most `size` chars, preferring newlines."""
    if len(text) <= size:
        return [text]
    out: list[str] = []
    buf: str = ""
    for line in text.splitlines(keepends=True):
        if len(buf) + len(line) > size:
            if buf:
                out.append(buf)
            buf = line
        else:
            buf += line
    if buf:
        out.append(buf)
    return out
