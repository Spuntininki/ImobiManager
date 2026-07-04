"""create addresses table

Revision ID: ea6e3df05e6e
Revises: 156e1646c9cd
Create Date: 2026-07-04 17:48:50.395591

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ea6e3df05e6e"
down_revision: str | Sequence[str] | None = "156e1646c9cd"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "addresses",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("street_name", sa.String(), nullable=False),
        sa.Column("number", sa.String(), nullable=False),
        sa.Column("complement", sa.String(), nullable=True),
        sa.Column("neighborhood", sa.String(), nullable=False),
        sa.Column("city", sa.String(), nullable=False),
        sa.Column("state", sa.String(), nullable=False),
        sa.Column("zip_code", sa.String(), nullable=False),
        sa.Column(
            "type",
            sa.Enum("HOUSE", "COMMERCIAL", name="property_type"),
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
    )


def downgrade() -> None:
    """Downgrade schema (forward-only policy — intentionally a no-op)."""
    pass
