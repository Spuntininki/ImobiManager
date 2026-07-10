"""consolidate contract file paths into single column

Replaces `unrecognized_contract_file_path` and `recognized_contract_file_path`
with a single `contract_file_path` column, migrating any existing data.

Revision ID: f7e2c4b0d1a9
Revises: 6b908c1fa526
Create Date: 2026-07-10 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f7e2c4b0d1a9"
down_revision: str | Sequence[str] | None = "6b908c1fa526"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema.

    1. Add the new nullable contract_file_path column.
    2. Migrate data: prefer recognized_contract_file_path, fall back to
       unrecognized_contract_file_path.
    3. Drop the two old columns.
    """
    op.add_column(
        "contracts",
        sa.Column("contract_file_path", sa.String(), nullable=True),
    )

    # Migrate existing data — take the recognized path if available,
    # otherwise the unrecognized one.
    op.execute(
        """UPDATE contracts
           SET contract_file_path = COALESCE(
               recognized_contract_file_path,
               unrecognized_contract_file_path
           )
           WHERE recognized_contract_file_path IS NOT NULL
              OR unrecognized_contract_file_path IS NOT NULL"""
    )

    op.drop_column("contracts", "recognized_contract_file_path")
    op.drop_column("contracts", "unrecognized_contract_file_path")


def downgrade() -> None:
    """Downgrade schema (forward-only policy — intentionally a no-op)."""
    pass
