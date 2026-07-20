"""Tests for the MCP server tools (read-only, role-aware, subject-scoped).

The bot pod's MCP client sends headers identifying the subject. These tests
build a fake MCP `Context` carrying those headers and call the tool functions
directly — bypassing the HTTP transport — to assert scoping rules.
"""

from contextlib import AbstractAsyncContextManager
from typing import Any

import pytest
from mcp.server.fastmcp import Context
from mcp.server.fastmcp.exceptions import ToolError
from mcp.shared.context import RequestContext
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.datastructures import Headers

from app.core.security import hash_password
from app.mcp import server as mcp_server
from app.models.address import Address
from app.models.contract import Contract
from app.models.enums import ContractStatus, PropertyType
from app.models.owner import Owner
from app.models.owner_renter import OwnerRenter
from app.models.renter import Renter
from app.models.user import User
from app.models.user_owner import UserOwner

from .conftest import TEST_BOT_API_KEY


class _BorrowedSession(AbstractAsyncContextManager):
    """Yields the shared savepoint-bound test session without closing it.

    Monkey-patched in place of `app.mcp.server._session` so MCP tools see the
    same data the test seeded via `db_session`.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def __aenter__(self) -> AsyncSession:
        return self._session

    async def __aexit__(self, *exc: object) -> None:
        return None


def _ctx(
    subject_type: str,
    subject_id: int,
    api_key: str = TEST_BOT_API_KEY,
) -> Context:
    """Build an MCP `Context` carrying the bot pod's per-request headers."""
    headers = Headers(
        {
            "x-bot-api-key": api_key,
            "x-bot-subject-type": subject_type,
            "x-bot-subject-id": str(subject_id),
        }
    )

    class _FakeRequest:
        __slots__ = ("headers",)

        def __init__(self, h: Headers) -> None:
            self.headers = h

    rc = RequestContext(
        request_id="test",
        meta=None,
        session=None,  # type: ignore[arg-type]
        lifespan_context=None,
        request=_FakeRequest(headers),
    )
    return Context(request_context=rc)


@pytest.fixture
def mcp_session(db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch) -> AsyncSession:
    """Redirect the MCP tools' session factory to the test savepoint session.

    The real `_session()` is a coroutine returning an `AsyncSession`. We mirror
    that signature so the tool's `async with await _session() as session:`
    pattern keeps working.
    """

    async def _factory() -> _BorrowedSession:
        return _BorrowedSession(db_session)

    monkeypatch.setattr(mcp_server, "_session", _factory)
    return db_session


# --- Seeding helpers --------------------------------------------------------


async def _seed_user_with_owner(
    session: AsyncSession,
) -> tuple[User, Owner, Renter, Address, Contract]:
    user = User(email="u@test.com", name="U", password=hash_password("x"))
    session.add(user)
    await session.flush()
    owner = Owner(name="Owner One")
    session.add(owner)
    await session.flush()
    session.add(UserOwner(user_id=user.id, owner_id=owner.id))
    renter = Renter(name="Maria", primary_contact="+55 11 9999-0000")
    session.add(renter)
    await session.flush()
    session.add(OwnerRenter(owner_id=owner.id, renter_id=renter.id))
    address = Address(
        owner_id=owner.id,
        street_name="Rua X",
        number="123",
        neighborhood="Centro",
        city="São Paulo",
        state="SP",
        zip_code="01000-000",
        type=PropertyType.HOUSE,
    )
    session.add(address)
    await session.flush()
    from datetime import datetime

    contract = Contract(
        owner_id=owner.id,
        renter_id=renter.id,
        address_id=address.id,
        start_date=datetime(2025, 1, 1),
        end_date=datetime(2026, 12, 31),
        monthly_revenue=1500,
        deposit_value=1500,
        deposit_months=1,
        payment_day=5,
        status=ContractStatus.ACTIVE,
    )
    session.add(contract)
    await session.commit()
    await session.refresh(user)
    await session.refresh(owner)
    await session.refresh(renter)
    await session.refresh(address)
    await session.refresh(contract)
    return user, owner, renter, address, contract


# --- Auth + subject header checks -------------------------------------------


async def test_tool_rejects_missing_api_key(mcp_session: AsyncSession) -> None:
    with pytest.raises(ToolError):
        await mcp_server.list_owners(_ctx("USER", 1, api_key=""))


async def test_tool_rejects_wrong_api_key(mcp_session: AsyncSession) -> None:
    with pytest.raises(ToolError):
        await mcp_server.list_owners(_ctx("USER", 1, api_key="wrong"))


async def test_tool_rejects_missing_subject_headers(mcp_session: AsyncSession) -> None:
    # Build a ctx whose headers omit subject fields.
    headers = Headers({"x-bot-api-key": TEST_BOT_API_KEY})

    class _FakeRequest:
        __slots__ = ("headers",)

        def __init__(self, h: Headers) -> None:
            self.headers = h

    rc = RequestContext(
        request_id="t",
        meta=None,
        session=None,
        lifespan_context=None,
        request=_FakeRequest(headers),
    )
    ctx = Context(request_context=rc)
    with pytest.raises(ToolError):
        await mcp_server.list_owners(ctx)


# --- USER scoping -----------------------------------------------------------


async def test_user_list_owners_returns_only_linked(mcp_session: AsyncSession) -> None:
    user, owner, *_ = await _seed_user_with_owner(mcp_session)
    # An owner NOT linked to the user.
    stranger = Owner(name="Stranger")
    mcp_session.add(stranger)
    await mcp_session.commit()

    ctx = _ctx("USER", user.id)
    result = await mcp_server.list_owners(ctx)
    assert [o["id"] for o in result] == [owner.id]


async def test_user_list_active_contracts(mcp_session: AsyncSession) -> None:
    user, _, _, _, contract = await _seed_user_with_owner(mcp_session)
    ctx = _ctx("USER", user.id)
    result = await mcp_server.list_active_contracts(ctx)
    assert [c["id"] for c in result] == [contract.id]
    assert result[0]["status"] == "ACTIVE"


async def test_user_get_renter_unrelated_rejects(mcp_session: AsyncSession) -> None:
    user, _, renter, *_ = await _seed_user_with_owner(mcp_session)
    stranger = Renter(name="Outsider", primary_contact="+55 11 0000-0000")
    mcp_session.add(stranger)
    await mcp_session.commit()

    ctx = _ctx("USER", user.id)
    ok = await mcp_server.get_renter(ctx, renter_id=renter.id)
    assert ok["id"] == renter.id

    with pytest.raises(ToolError):
        await mcp_server.get_renter(ctx, renter_id=stranger.id)


# --- RENTER scoping ---------------------------------------------------------


async def test_renter_scoped_contracts_and_owner_rejection(mcp_session: AsyncSession) -> None:
    _, owner, renter, address, contract = await _seed_user_with_owner(mcp_session)

    ctx = _ctx("RENTER", renter.id)
    # Only contracts where renter_id == subject_id.
    contracts = await mcp_server.list_active_contracts(ctx)
    assert [c["id"] for c in contracts] == [contract.id]

    # Addresses only on the renter's contracts.
    addresses: list[dict[str, Any]] = await mcp_server.list_addresses(ctx)
    assert [a["id"] for a in addresses] == [address.id]

    # get_renter(self) ok; other → ToolError.
    me = await mcp_server.get_renter(ctx, renter_id=renter.id)
    assert me["id"] == renter.id
    with pytest.raises(ToolError):
        await mcp_server.get_renter(ctx, renter_id=renter.id + 9999)

    # list_owners is USER-only.
    with pytest.raises(ToolError):
        await mcp_server.list_owners(ctx)
