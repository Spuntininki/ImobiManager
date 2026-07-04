"""create renter_documents table

Revision ID: 156e1646c9cd
Revises: ebcf795d4749
Create Date: 2026-07-04 17:36:03.253172

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "156e1646c9cd"
down_revision: str | Sequence[str] | None = "ebcf795d4749"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "renter_documents",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("renter_id", sa.Integer(), nullable=False),
        sa.Column("document", sa.String(), nullable=False),
        sa.Column(
            "document_type",
            sa.Enum("RG", "CPF", "CNPJ", name="document_types"),
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
        sa.ForeignKeyConstraint(["renter_id"], ["renters.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("renter_id", "document_type", name="uq_renter_documents_renter_type"),
    )


def downgrade() -> None:
    """Downgrade schema (forward-only policy — intentionally a no-op)."""
    pass
