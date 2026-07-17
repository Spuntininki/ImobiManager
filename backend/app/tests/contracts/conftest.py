"""Pytest fixtures scoped to the contracts test folder."""

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contract_template import ContractTemplate
from app.services.contract_generation.default_template import (
    STANDARD_TEMPLATE_CODE,
    STANDARD_TEMPLATE_DESCRIPTION,
    load_default_content,
    load_default_style,
)


@pytest_asyncio.fixture
async def seeded_standard_template(db_session: AsyncSession) -> ContractTemplate:
    """Insert the 'standard' contract template row for tests that need it.

    Uses the same payload the Alembic migration seeds in production, so the
    test-time row is byte-identical to the migration seed. Rolls back with
    the per-test savepoint, so each test starts with no template rows
    unless it pulls in this fixture.
    """
    template = ContractTemplate(
        code=STANDARD_TEMPLATE_CODE,
        description=STANDARD_TEMPLATE_DESCRIPTION,
        content=load_default_content(),
        style=load_default_style(),
        is_active=True,
    )
    db_session.add(template)
    await db_session.commit()
    await db_session.refresh(template)
    return template
