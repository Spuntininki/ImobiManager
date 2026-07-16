"""create contract_templates table

Stores the contract template (``content``) and style (``style``) as JSONB,
keyed by ``code``. Seeds the single 'standard' row from
``default_template.DEFAULT_CONTENT_JSON`` / ``DEFAULT_STYLE_JSON``.

The ``ContractTemplate`` ORM model (see ``app.models.contract_template``) is
the runtime mirror; this migration creates the table so the seed payload can
be inserted in the same transaction.

Revision ID: 9a5c1df5395f
Revises: f7e2c4b0d1a9
Create Date: 2026-07-15 22:30:00.000000

"""

import json
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9a5c1df5395f"
down_revision: str | Sequence[str] | None = "f7e2c4b0d1a9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema.

    1. Create the ``contract_templates`` table.
    2. Seed the single 'standard' row from the inlined JSON strings in
       ``default_template``.
    """
    op.create_table(
        "contract_templates",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("content", sa.dialects.postgresql.JSONB(), nullable=False),
        sa.Column("style", sa.dialects.postgresql.JSONB(), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_contract_templates_code"),
    )

    # Import here so the migration file can be inspected without requiring
    # the backend application to be fully importable at registration time.
    from app.services.contract_generation.default_template import (
        STANDARD_TEMPLATE_CODE,
        STANDARD_TEMPLATE_DESCRIPTION,
        load_default_content,
        load_default_style,
    )

    op.execute(
        sa.text(
            """
            INSERT INTO contract_templates (code, description, content, style, is_active)
            VALUES (:code, :description, CAST(:content AS jsonb), CAST(:style AS jsonb), TRUE)
            """
        ).bindparams(
            sa.bindparam("code", value=STANDARD_TEMPLATE_CODE, type_=sa.String()),
            sa.bindparam(
                "description", value=STANDARD_TEMPLATE_DESCRIPTION, type_=sa.Text()
            ),
            sa.bindparam(
                "content", value=json.dumps(load_default_content()), type_=sa.Text()
            ),
            sa.bindparam(
                "style", value=json.dumps(load_default_style()), type_=sa.Text()
            ),
        )
    )


def downgrade() -> None:
    """Downgrade schema (forward-only policy — intentionally a no-op)."""
    pass
