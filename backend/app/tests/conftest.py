"""Shared pytest fixtures for the ImobiManager backend test suite."""

import asyncio
from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.db.session import get_db
from app.main import app
from app.models.address import Address  # noqa: F401 — registers table on metadata
from app.models.base import Base  # noqa: F401 — used by _reset_test_schema
from app.models.contract import Contract  # noqa: F401
from app.models.contract_template import ContractTemplate  # noqa: F401
from app.models.owner import Owner  # noqa: F401
from app.models.owner_document import OwnerDocument  # noqa: F401
from app.models.owner_renter import OwnerRenter  # noqa: F401
from app.models.renter import Renter  # noqa: F401
from app.models.renter_document import RenterDocument  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.user_owner import UserOwner  # noqa: F401

# --- Test engine bound to the test database ---
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
async def db_connection_session() -> AsyncGenerator[tuple[AsyncConnection, AsyncSession]]:
    """Shared connection + outer transaction + savepoint session per test.

    Both db_session and client bind to this single connection so that data
    seeded via db_session is visible to requests made via client. The outer
    transaction rolls back at teardown so tests never leak data into each
    other.
    """
    connection = await test_engine.connect()
    transaction = await connection.begin()
    session = AsyncSession(
        bind=connection,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    try:
        yield connection, session
    finally:
        await session.close()
        await transaction.rollback()
        await connection.close()


@pytest_asyncio.fixture
async def db_session(
    db_connection_session: tuple[AsyncConnection, AsyncSession],
) -> AsyncSession:
    """Per-test async session bound to the shared savepoint transaction."""
    _, session = db_connection_session
    return session


@pytest_asyncio.fixture
async def client(
    db_connection_session: tuple[AsyncConnection, AsyncSession],
) -> AsyncGenerator[AsyncClient]:
    """HTTP client with get_db overridden to the shared savepoint session.

    Service commits release savepoints (not the outer transaction), so data
    is visible across requests within the same test and rolled back entirely
    at teardown.
    """
    _, session = db_connection_session

    async def get_test_db() -> AsyncGenerator[AsyncSession]:
        yield session

    app.dependency_overrides[get_db] = get_test_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def seeded_standard_template(db_session: AsyncSession) -> ContractTemplate:
    """Insert the 'standard' contract template row for tests that need it.

    Uses the same payload the Alembic migration seeds in production, so the
    test-time row is byte-identical to the migration seed. Rolls back with
    the per-test savepoint, so each test starts with no template rows
    unless it pulls in this fixture.
    """
    from app.services.contract_generation.default_template import (
        STANDARD_TEMPLATE_CODE,
        STANDARD_TEMPLATE_DESCRIPTION,
        load_default_content,
        load_default_style,
    )

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
