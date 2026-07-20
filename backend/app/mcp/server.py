"""ImobiManager MCP server (read-only, role-aware).

Mounted by the FastAPI app at `POST /mcp`. The bot pod is the only client.
Per request it must send:

- `X-Bot-Api-Key: <BOT_MCP_API_KEY>` (shared secret) — verified inside every
  tool call via `_require_authed_subject`.
- `X-Bot-Subject-Type: USER|RENTER`
- `X-Bot-Subject-Id: <int>`

The bot pod obtains subject info from `POST /api/v1/bot/auth/validate` and
forwards it as headers on every MCP request. The LLM therefore cannot forge
the subject: it only controls tool arguments, never HTTP headers.

All tools are read-only. Scoping rules:
- USER → rows reachable through `user_owners` (owners, addresses on those
  owners, contracts on those owners, renters linked via owner_renters).
- RENTER → rows reachable through `contracts.renter_id == subject_id`
  (own contracts and the addresses on them) plus the renter's own row.
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import Context, FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.server.transport_security import TransportSecuritySettings
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import async_session_factory
from app.models.address import Address
from app.models.contract import Contract
from app.models.enums import BotSubjectType, ContractStatus
from app.models.owner import Owner
from app.models.owner_renter import OwnerRenter
from app.models.renter import Renter
from app.models.user_owner import UserOwner

mcp = FastMCP(
    "ImobiManager",
    streamable_http_path="/",
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=False,
        allowed_hosts=["*"],
        allowed_origins=["*"],
    ),
)


def _subject_from_ctx(ctx: Context) -> tuple[BotSubjectType, int]:
    """Return (subject_type, subject_id) from request headers.

    Verifies the `X-Bot-Api-Key` shared secret. Any failure raises ToolError
    so the bot sees a clean error message instead of leaking protocol details.
    """
    request = ctx.request_context.request
    if request is None:  # pragma: no cover — defensive, streamable_http always sets it
        raise ToolError("Missing request context")
    headers = request.headers
    if not settings.bot_mcp_api_key:
        raise ToolError("MCP server not configured")
    api_key = headers.get("x-bot-api-key")
    if api_key != settings.bot_mcp_api_key:
        raise ToolError("Unauthorized")
    raw_type = headers.get("x-bot-subject-type")
    raw_id = headers.get("x-bot-subject-id")
    if raw_type is None or raw_id is None:
        raise ToolError("Missing subject headers")
    try:
        subject_type = BotSubjectType(raw_type)
        subject_id = int(raw_id)
    except (ValueError, TypeError) as exc:
        raise ToolError("Invalid subject headers") from exc
    return subject_type, subject_id


async def _session() -> AsyncSession:
    """Open a short-lived async DB session for a tool call."""
    return async_session_factory()


# --- Tools -------------------------------------------------------------------


@mcp.tool()
async def list_owners(ctx: Context) -> list[dict[str, Any]]:
    """List property owners the caller is allowed to manage (USER only).

    Returns owner id and legal/business name. RENTER subjects have no owners
    to list and get a ToolError.
    """
    subject_type, subject_id = _subject_from_ctx(ctx)
    if subject_type is not BotSubjectType.USER:
        raise ToolError("list_owners is only available for USER subjects")
    async with await _session() as session:
        result = await session.execute(
            select(Owner)
            .join(UserOwner, UserOwner.owner_id == Owner.id)
            .where(UserOwner.user_id == subject_id)
            .order_by(Owner.id)
        )
        return [{"id": o.id, "name": o.name} for o in result.scalars().all()]


@mcp.tool()
async def list_addresses(ctx: Context) -> list[dict[str, Any]]:
    """List properties (addresses) reachable by the caller.

    USER: every address whose owner is managed by the user.
    RENTER: every address on an active or pending contract where
    `renter_id == subject_id`.
    """
    subject_type, subject_id = _subject_from_ctx(ctx)
    async with await _session() as session:
        if subject_type is BotSubjectType.USER:
            result = await session.execute(
                select(Address)
                .join(Owner, Owner.id == Address.owner_id)
                .join(UserOwner, UserOwner.owner_id == Owner.id)
                .where(UserOwner.user_id == subject_id)
                .order_by(Address.id)
            )
            rows = result.scalars().all()
        else:
            result = await session.execute(
                select(Address)
                .join(Contract, Contract.address_id == Address.id)
                .where(Contract.renter_id == subject_id)
                .order_by(Address.id)
            )
            rows = result.scalars().all()
        return [_address_dict(a) for a in rows]


@mcp.tool()
async def list_active_contracts(ctx: Context) -> list[dict[str, Any]]:
    """List active contracts reachable by the caller.

    USER: contracts whose owner is managed by the user and status=ACTIVE.
    RENTER: contracts where `renter_id == subject_id` and status=ACTIVE.
    """
    subject_type, subject_id = _subject_from_ctx(ctx)
    async with await _session() as session:
        if subject_type is BotSubjectType.USER:
            result = await session.execute(
                select(Contract)
                .join(UserOwner, UserOwner.owner_id == Contract.owner_id)
                .where(
                    UserOwner.user_id == subject_id,
                    Contract.status == ContractStatus.ACTIVE,
                )
                .order_by(Contract.id)
            )
        else:
            result = await session.execute(
                select(Contract)
                .where(
                    Contract.renter_id == subject_id,
                    Contract.status == ContractStatus.ACTIVE,
                )
                .order_by(Contract.id)
            )
        return [_contract_dict(c) for c in result.scalars().all()]


@mcp.tool()
async def get_renter(ctx: Context, renter_id: int) -> dict[str, Any]:
    """Return a single renter's contact info.

    USER: the renter must be linked to one of the user's owners via
    `owner_renters`; otherwise ToolError.
    RENTER: the renter_id must equal the caller's own subject_id.
    """
    subject_type, subject_id = _subject_from_ctx(ctx)
    if subject_type is BotSubjectType.RENTER and renter_id != subject_id:
        raise ToolError("Renters can only query their own record")
    async with await _session() as session:
        renter = await session.get(Renter, renter_id)
        if renter is None:
            raise ToolError("Renter not found")
        if subject_type is BotSubjectType.USER:
            link = await session.execute(
                select(OwnerRenter)
                .join(UserOwner, UserOwner.owner_id == OwnerRenter.owner_id)
                .where(
                    UserOwner.user_id == subject_id,
                    OwnerRenter.renter_id == renter_id,
                )
            )
            if link.scalar_one_or_none() is None:
                raise ToolError("Renter not found")
        return _renter_dict(renter)


# --- Helpers ----------------------------------------------------------------


def _address_dict(a: Address) -> dict[str, Any]:
    return {
        "id": a.id,
        "owner_id": a.owner_id,
        "street_name": a.street_name,
        "number": a.number,
        "complement": a.complement,
        "neighborhood": a.neighborhood,
        "city": a.city,
        "state": a.state,
        "zip_code": a.zip_code,
        "type": str(a.type),
    }


def _contract_dict(c: Contract) -> dict[str, Any]:
    return {
        "id": c.id,
        "owner_id": c.owner_id,
        "renter_id": c.renter_id,
        "address_id": c.address_id,
        "start_date": c.start_date.isoformat(),
        "end_date": c.end_date.isoformat(),
        "monthly_revenue": float(c.monthly_revenue),
        "deposit_value": float(c.deposit_value),
        "deposit_months": c.deposit_months,
        "payment_day": c.payment_day,
        "status": str(c.status),
    }


def _renter_dict(r: Renter) -> dict[str, Any]:
    return {
        "id": r.id,
        "name": r.name,
        "primary_contact": r.primary_contact,
        "secondary_contact": r.secondary_contact,
        "email": r.email,
    }


def build_mcp_app():
    """Return the Starlette ASGI app exposing the MCP server.

    The FastAPI app mounts this at `/mcp`. Inner route is `/` so the mount's
    prefix strip results in matching both `/mcp` and `/mcp/`.
    """
    return mcp.streamable_http_app()
