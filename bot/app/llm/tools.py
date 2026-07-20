"""LangChain tools that wrap calls into the backend MCP server.

Each tool function delegates to an `mcp.ClientSession` obtained from a
module-level `ContextVar` set for the duration of one `agent.ainvoke` run.
This keeps the agent itself stateless and avoids rebuilding the graph per
message — the agent is built once at pod startup; only the ContextVar is
swapped per inbound message.

Tools exposed (mirror the backend's MCP tool set, all read-only):

- `list_owners`         — USER only (see guardrails)
- `list_addresses`      — USER and RENTER
- `list_active_contracts` — USER and RENTER
- `get_renter`          — USER and RENTER (renter_id arg)
"""

from __future__ import annotations

import json
from contextvars import ContextVar

from langchain_core.tools import tool
from mcp import ClientSession

# Set per run by `AgentRunner` before invoking the agent. The MCP session
# shares the X-Bot-Subject-* headers baked into the underlying HTTP
# transport, so subject scoping is enforced server-side.
_current_session: ContextVar[ClientSession] = ContextVar("mcp_session")


def set_session(session: ClientSession) -> object:
    """Set the per-run MCP session. Returns the token to reset it later."""
    return _current_session.set(session)


def reset_session(token: object) -> None:
    """Reset the per-run MCP session after the agent finished."""
    _current_session.reset(token)


def _session() -> ClientSession:
    return _current_session.get()


def _as_text(result) -> str:
    """Best-effort extraction of the textual content of a CallToolResult."""
    contents = getattr(result, "content", None) or []
    parts: list[str] = []
    for block in contents:
        text = getattr(block, "text", None)
        if isinstance(text, str) and text:
            parts.append(text)
    return "\n".join(parts) if parts else json.dumps(result.model_dump(), default=str)


@tool("list_owners")
async def list_owners() -> str:
    """List property owners the caller is allowed to manage (USER only).

    Returns owner id and legal/business name. RENTERs have no owners to list.
    """
    return await _call("list_owners", {})


@tool("list_addresses")
async def list_addresses() -> str:
    """List properties (addresses) reachable by the caller.

    USER: every address whose owner is managed by the caller.
    RENTER: every address on an active contract where renter_id is the caller.
    """
    return await _call("list_addresses", {})


@tool("list_active_contracts")
async def list_active_contracts() -> str:
    """List active contracts reachable by the caller.

    USER: contracts whose owner is managed by the caller.
    RENTER: contracts where renter_id is the caller.
    """
    return await _call("list_active_contracts", {})


@tool("get_renter")
async def get_renter(renter_id: int) -> str:
    """Return a single renter's contact info by id.

    USER: renter must be linked to one of the caller's owners.
    RENTER: renter_id must equal the caller's own subject id.
    """
    return await _call("get_renter", {"renter_id": renter_id})


async def _call(name: str, arguments: dict) -> str:
    """Invoke an MCP tool and return its textual content."""
    session = _session()
    result = await session.call_tool(name, arguments)
    return _as_text(result)


ALL_TOOLS = [list_owners, list_addresses, list_active_contracts, get_renter]
