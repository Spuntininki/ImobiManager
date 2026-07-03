"""Tests for the async DB session layer."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def test_session_can_execute_select_one(db_session: AsyncSession) -> None:
    """The async session fixture can run a trivial query against the test DB."""
    result = await db_session.execute(text("SELECT 1"))
    row = result.scalar_one()
    assert row == 1
