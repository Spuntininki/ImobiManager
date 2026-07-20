"""Buffered message-log publisher.

The bot accumulates audit entries in memory and flushes them in batches to
`POST /api/v1/bot/message-logs` on the backend:

- periodically (`bot_log_flush_interval` seconds), and
- when the buffer reaches `bot_log_flush_batch_size` entries.

`flush()` is best-effort: failures are logged and the batch is dropped. The
audit table is for offline analysis only — losing a flush should never break
the bot's runtime behavior.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class _PendingLog:
    token_id: int | None
    chat_id: int
    direction: str
    llm_tokens_used: int


class MessageLogPublisher:
    """Accumulates logs and flushes them to the backend in batches."""

    def __init__(self, http: httpx.AsyncClient) -> None:
        self._http = http
        self._buffer: list[_PendingLog] = []
        self._lock = asyncio.Lock()
        self._flush_task: asyncio.Task[None] | None = None
        self._stopping = False

    async def start(self) -> None:
        """Spawn the periodic flush loop."""
        self._flush_task = asyncio.create_task(self._periodic_flush())

    async def stop(self) -> None:
        """Stop the loop and flush whatever is still in the buffer."""
        self._stopping = True
        if self._flush_task is not None:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        await self._flush_now()

    def record(
        self,
        *,
        token_id: int | None,
        chat_id: int,
        direction: str,
        llm_tokens_used: int = 0,
    ) -> None:
        """Append one audit entry (non-blocking)."""
        if self._stopping:
            return
        self._buffer.append(
            _PendingLog(
                token_id=token_id,
                chat_id=chat_id,
                direction=direction,
                llm_tokens_used=llm_tokens_used,
            )
        )
        if len(self._buffer) >= settings.bot_log_flush_batch_size:
            asyncio.create_task(self._flush_now())

    async def _periodic_flush(self) -> None:
        while not self._stopping:
            await asyncio.sleep(settings.bot_log_flush_interval)
            await self._flush_now()

    async def _flush_now(self) -> None:
        async with self._lock:
            if not self._buffer:
                return
            batch = self._buffer[: settings.bot_log_flush_batch_size]
            self._buffer = self._buffer[len(batch) :]
        if not batch:
            return
        url = f"{settings.bot_backend_base_url}/api/v1/bot/message-logs"
        body = {
            "logs": [
                {
                    "token_id": b.token_id,
                    "chat_id": b.chat_id,
                    "direction": b.direction,
                    "llm_tokens_used": b.llm_tokens_used,
                }
                for b in batch
            ]
        }
        try:
            await self._http.post(
                url,
                json=body,
                headers={"X-Bot-Api-Key": settings.bot_mcp_api_key},
            )
        except httpx.HTTPError as exc:
            logger.warning("message-log flush failed: %s", exc)
