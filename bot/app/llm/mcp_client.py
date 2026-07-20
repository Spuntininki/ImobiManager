"""MCP client over Streamable HTTP.

Per inbound LLM-bound message we open a fresh MCP session against the
backend's `/mcp` endpoint:

1. `streamablehttp_client()` returns `(read, write, get_session_id)`.
2. Wrap it in `ClientSession`, `initialize()`.
3. The session lives for the duration of one `AgentExecutor.invoke` run; all
   tools in that run share the same session (and thus the same
   `X-Bot-Subject-*` headers, set once on the transport).
4. The context manager closes everything on exit.

Reopening per message keeps the bot stateless per chat (no idle session pool
to manage) at the cost of one extra `initialize` round-trip — acceptable
for the MVP single-pod deployment.

The subject is authoritative: it is read from the validated `AuthResult`
upstream and turned into HTTP headers here, so the LLM (which only decides
which tool to call and with what arguments) cannot forge the subject.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from app.config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def connect(
    *,
    subject_type: str,
    subject_id: int,
) -> AsyncIterator[ClientSession]:
    """Open and initialize an MCP `ClientSession` for one agent run."""
    headers = {
        "X-Bot-Api-Key": settings.bot_mcp_api_key,
        "X-Bot-Subject-Type": subject_type,
        "X-Bot-Subject-Id": str(subject_id),
    }
    url = f"{settings.bot_backend_base_url}/mcp"
    async with streamablehttp_client(url, headers=headers) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session
