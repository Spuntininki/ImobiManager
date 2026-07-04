"""create owner_documents table

Revision ID: bf7c9033fbc3
Revises: ea6e3df05e6e
Create Date: 2026-07-04 18:02:32.766195

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "bf7c9033fbc3"
down_revision: str | Sequence[str] | None = "ea6e3df05e6e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # The `document_types` enum already exists from the renter_documents
    # migration (156e1646c9cd). Create the type idempotently via a DO block
    # (PostgreSQL doesn't support IF NOT EXISTS for CREATE TYPE directly),
    # then disable SQLAlchemy's automatic re-creation via create_type=False.
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_type WHERE typname = 'document_types'
            ) THEN
                CREATE TYPE document_types AS ENUM ('RG', 'CPF', 'CNPJ');
            END IF;
        END
        $$
        """
    )

    op.create_table(
        "owner_documents",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("document", sa.String(), nullable=False),
        sa.Column(
            "document_type",
            PG_ENUM("RG", "CPF", "CNPJ", name="document_types", create_type=False),
            nullable=False,
        ),
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
        sa.ForeignKeyConstraint(["owner_id"], ["owners.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("owner_id", "document_type", name="uq_owner_documents_owner_type"),
    )


def downgrade() -> None:
    """Downgrade schema (forward-only policy — intentionally a no-op)."""
    pass
