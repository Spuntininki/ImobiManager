"""create contracts table

Revision ID: 4ae7f281a996
Revises: bf7c9033fbc3
Create Date: 2026-07-06 14:48:06.340816

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4ae7f281a996"
down_revision: str | Sequence[str] | None = "bf7c9033fbc3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "contracts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("renter_id", sa.Integer(), nullable=False),
        sa.Column("address_id", sa.Integer(), nullable=False),
        sa.Column("start_date", sa.DateTime(), nullable=False),
        sa.Column("end_date", sa.DateTime(), nullable=False),
        sa.Column(
            "monthly_revenue",
            sa.Numeric(precision=12, scale=2),
            nullable=False,
        ),
        sa.Column("deposit_value", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("deposit_months", sa.Integer(), nullable=False),
        sa.Column(
            "generation_date",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("signed_date", sa.DateTime(), nullable=True),
        sa.Column("cancel_date", sa.DateTime(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("PENDING", "ACTIVE", "EXPIRED", "CANCELLED", name="contract_status"),
            nullable=False,
        ),
        sa.Column("unrecognized_contract_file_path", sa.String(), nullable=True),
        sa.Column("recognized_contract_file_path", sa.String(), nullable=True),
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
        sa.ForeignKeyConstraint(["address_id"], ["addresses.id"]),
        sa.ForeignKeyConstraint(["owner_id"], ["owners.id"]),
        sa.ForeignKeyConstraint(["renter_id"], ["renters.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema (forward-only policy — intentionally a no-op)."""
    pass
