"""Telegram polling entrypoint.

Adapts the raw `update` dicts coming from `TelegramClient.poll_updates()` into
`InboundMessage` dataclasses the router knows how to handle, then dispatches
to a `MessageRouter`. The poller owns no business logic.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from app.platforms.telegram.client import TelegramClient
from app.platforms.telegram.types import InboundMessage

if TYPE_CHECKING:  # avoid runtime circular import
    from app.router import MessageRouter

logger = logging.getLogger(__name__)


def _parse(update: dict) -> InboundMessage | None:
    """Return an InboundMessage or None for updates the bot ignores.

    The bot currently handles only `message.text` updates. Anything else
    (stickers, edited messages, channel posts, callback queries, etc.) is
    silently dropped — the answer is to keep the LLM usage focused on text.
    """
    message = update.get("message")
    if not isinstance(message, dict):
        return None
    chat = message.get("chat", {})
    chat_id = chat.get("id")
    text = message.get("text")
    if not isinstance(chat_id, int) or not isinstance(text, str):
        return None
    return InboundMessage(update_id=int(update["update_id"]), chat_id=chat_id, text=text)


async def run_polling(tg: TelegramClient, router: MessageRouter) -> None:
    """Long-poll Telegram forever and route parsed messages.

    Concurrency model: each inbound message is dispatched as a background
    task so polling is not blocked by a slow LLM call. A single `RateLimiter`
    lock per token_id ensures neither requests nor LLM calls for the same
    client overlap. Higher-level concurrency (multiple agents) is intentionally
    out of scope for the MVP (see plan).
    """
    async for update in tg.poll_updates():
        parsed = _parse(update)
        if parsed is None:
            continue
        asyncio.create_task(_safe_route(tg, router, parsed))


async def _safe_route(tg: TelegramClient, router: MessageRouter, msg: InboundMessage) -> None:
    try:
        await router.route(msg, tg)
    except Exception:  # pragma: no cover — defensive, the router swallows most
        logger.exception("unhandled error routing message chat_id=%s", msg.chat_id)
