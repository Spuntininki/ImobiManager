"""create renters table

Revision ID: 9e298b75af78
Revises: a1fb0332ce9d
Create Date: 2026-07-04 16:09:47.296828

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9e298b75af78"
down_revision: str | Sequence[str] | None = "a1fb0332ce9d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "renters",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("primary_contact", sa.String(), nullable=False),
        sa.Column("secondary_contact", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("renters")
