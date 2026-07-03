"""Shared pytest fixtures for the ImobiManager backend test suite."""

import asyncio
from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.db.session import get_db
from app.main import app
from app.models.base import Base
from app.models.owner import Owner  # noqa: F401 — registers table on metadata

# --- Test engine bound to the test database (never commits in tests) ---
test_engine = create_async_engine(
    settings.test_database_url,
    pool_pre_ping=True,
    future=True,
    poolclass=NullPool,
)
test_session_factory = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


def _reset_test_schema() -> None:
    """Drop and recreate all tables on the test database once per session.

    Implements the hybrid pattern: the database persists (created by
    docker-compose init.sql), but the schema is reset from metadata at the
    start of every pytest run so each run starts from a clean slate.
    """

    async def _run() -> None:
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(_run())


_reset_test_schema()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession]:
    """Per-test async session with rollback, for direct DB access tests."""
    async with test_session_factory() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient]:
    """HTTP client with get_db overridden to use a test-DB savepoint session.

    Each test runs inside a single outer transaction on the test DB. Service
    commits release savepoints (not the outer transaction), so data is
    visible across requests within the same test but rolled back entirely
    at teardown — no leakage between tests.
    """
    connection = await test_engine.connect()
    transaction = await connection.begin()
    session = AsyncSession(
        bind=connection,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )

    async def get_test_db() -> AsyncGenerator[AsyncSession]:
        yield session

    app.dependency_overrides[get_db] = get_test_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
    await transaction.rollback()
    await connection.close()
