"""add payment_day to contracts

Revision ID: 6b908c1fa526
Revises: 4ae7f281a996
Create Date: 2026-07-08 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6b908c1fa526"
down_revision: str | Sequence[str] | None = "4ae7f281a996"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "contracts",
        sa.Column("payment_day", sa.Integer(), nullable=False, server_default="1"),
    )
    op.alter_column("contracts", "payment_day", server_default=None)


def downgrade() -> None:
    """Downgrade schema (forward-only policy — intentionally a no-op)."""
    pass
