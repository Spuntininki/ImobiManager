"""BotToken ORM model mirroring the `bot_tokens` table in schema.dbml."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.enums import BotSubjectType, BotTokenStatus


class BotToken(Base):
    """Auth token binding a chat platform account to a system subject.

    Polymorphic over `subject_type` + `subject_id` (no FK): USER → users.id,
    RENTER → renters.id. The `chat_id` is bound on the first `/start <token>`.
    """

    __tablename__ = "bot_tokens"
    __table_args__ = (
        Index("ix_bot_tokens_subject_type_subject_id", "subject_type", "subject_id"),
        Index("ix_bot_tokens_chat_id", "chat_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    token: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    subject_type: Mapped[BotSubjectType] = mapped_column(
        Enum(BotSubjectType, name="bot_subject_type"), nullable=False
    )
    subject_id: Mapped[int] = mapped_column(nullable=False)
    chat_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    status: Mapped[BotTokenStatus] = mapped_column(
        Enum(BotTokenStatus, name="bot_token_status"), nullable=False
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
