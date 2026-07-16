"""ContractTemplate ORM model — DB-backed contract template + style config.

Stores the JSON ``content`` (template lines with ``<REPLACE>`` tokens) and
``style`` (paragraph and table styling) for a contract layout, so non-developers
can edit contract wording via SQL/UI without a code deploy. Formatters stay in
code; only the prose/tokens live here.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ContractTemplate(Base):
    """A contract layout (template + style) keyed by ``code``.

    The ``standard`` row ships via migration seed (see ``default_template``).
    Future rows ('commercial', 'rural', owner-specific overrides) can be added
    by admins without a deploy, as long as they only combine existing tokens.
    """

    __tablename__ = "contract_templates"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[dict] = mapped_column(JSONB, nullable=False)
    style: Mapped[dict] = mapped_column(JSONB, nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, server_default=text("true"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
