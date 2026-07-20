"""Business logic for bot message logs (audit/cost tracking).

The bot pod batches logs and POSTs them fire-and-forget. This service just
appends rows; nothing reads them at runtime (analysis is offline-only).
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bot_message_log import BotMessageLog
from app.models.enums import MessageDirection
from app.schemas.bot import MessageLogCreate


async def append_logs(session: AsyncSession, logs: list[MessageLogCreate]) -> int:
    """Insert a batch of message log rows. Returns the number inserted.

    `token_id` is stored as-is (null for unauthenticated messages). The
    service trusts the bot pod for the foreign key; PG will reject unknown
    token ids at insert time.
    """
    if not logs:
        return 0
    rows = [
        BotMessageLog(
            token_id=log.token_id,
            chat_id=log.chat_id,
            direction=MessageDirection(log.direction),
            llm_tokens_used=log.llm_tokens_used,
        )
        for log in logs
    ]
    session.add_all(rows)
    await session.commit()
    return len(rows)
