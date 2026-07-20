"""create bot_tokens and bot_message_logs tables

Revision ID: 5573304d87a1
Revises: a770ded279e5
Create Date: 2026-07-20 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5573304d87a1"
down_revision: str | Sequence[str] | None = "a770ded279e5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema.

    Adds the enums and tables backing the Telegram bot: `bot_tokens` (auth
    tokens, polymorphic over USER/RENTER) and `bot_message_logs` (audit and
    cost tracking). Forward-only: no downgrade is maintained.
    """
    op.create_table(
        "bot_tokens",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("token", sa.String(), nullable=False),
        sa.Column(
            "subject_type",
            sa.Enum("USER", "RENTER", name="bot_subject_type"),
            nullable=False,
        ),
        sa.Column("subject_id", sa.Integer(), nullable=False),
        sa.Column("chat_id", sa.BigInteger(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("ACTIVE", "REVOKED", name="bot_token_status"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("token", name="uq_bot_tokens_token"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_bot_tokens_subject_type_subject_id",
        "bot_tokens",
        ["subject_type", "subject_id"],
    )
    op.create_index("ix_bot_tokens_chat_id", "bot_tokens", ["chat_id"])

    op.create_table(
        "bot_message_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("token_id", sa.Integer(), nullable=True),
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "direction",
            sa.Enum("IN", "OUT", name="message_direction"),
            nullable=False,
        ),
        sa.Column("llm_tokens_used", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["token_id"], ["bot_tokens.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema (forward-only policy — intentionally a no-op)."""
    pass
