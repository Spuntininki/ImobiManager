"""BotMessageLog ORM model mirroring the `bot_message_logs` table in schema.dbml."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.enums import MessageDirection


class BotMessageLog(Base):
    """Audit entry for messages exchanged with the chat platform.

    Persisted by the bot pod to support cost/abuse analysis. The in-memory
    rate limiter is authoritative at runtime; this table is the durable record.
    """

    __tablename__ = "bot_message_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    token_id: Mapped[int | None] = mapped_column(ForeignKey("bot_tokens.id"), nullable=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    direction: Mapped[MessageDirection] = mapped_column(
        Enum(MessageDirection, name="message_direction"), nullable=False
    )
    llm_tokens_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
