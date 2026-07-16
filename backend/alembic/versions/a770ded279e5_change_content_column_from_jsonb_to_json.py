"""change content column from jsonb to json

PostgreSQL JSONB sorts dictionary keys alphabetically, which corrupts the
section ordering (title → paragraphs → sign) in the template content.
Switching to the JSON type preserves key insertion order so the renderer
outputs sections in the correct sequence.

Revision ID: a770ded279e5
Revises: 9a5c1df5395f
Create Date: 2026-07-15 21:40:52.813206

"""

import json
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a770ded279e5"
down_revision: str | Sequence[str] | None = "9a5c1df5395f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema.

    1. Change the ``content`` column from JSONB to JSON (preserves key order).
    2. Re-write the 'standard' row with properly-ordered JSON content.
    """
    op.alter_column(
        "contract_templates",
        "content",
        type_=sa.dialects.postgresql.JSON(),
        postgresql_using="content::json",
    )

    # Re-seed the standard row with correctly ordered content.
    from app.services.contract_generation.default_template import (
        STANDARD_TEMPLATE_CODE,
        load_default_content,
    )

    op.execute(
        sa.text(
            """
            UPDATE contract_templates
            SET content = CAST(:content AS json)
            WHERE code = :code
            """
        ).bindparams(
            sa.bindparam("code", value=STANDARD_TEMPLATE_CODE, type_=sa.String()),
            sa.bindparam(
                "content", value=json.dumps(load_default_content()), type_=sa.Text()
            ),
        )
    )


def downgrade() -> None:
    """Downgrade schema (forward-only policy — intentionally a no-op)."""
    pass
