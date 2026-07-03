"""Shared pytest fixtures for the ImobiManager backend test suite."""

from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from app.main import app


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    """Async HTTP client wired to the FastAPI app via in-memory ASGI transport."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# Test engine is bound to the test database and never commits; every test runs
# inside a transaction that rolls back on teardown so tests stay isolated.
test_engine = create_async_engine(settings.test_database_url, pool_pre_ping=True, future=True)
test_session_factory = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession]:
    """Per-test async session that rolls back after the test completes."""
    async with test_session_factory() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()
