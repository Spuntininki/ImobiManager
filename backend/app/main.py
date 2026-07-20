"""FastAPI application entrypoint."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.mcp import build_mcp_app, mcp

# Build the MCP Starlette app eagerly so the session manager is initialized
# before the FastAPI lifespan starts. Mounting does not propagate the
# sub-app's lifespan, so we run the MCP session manager inside the FastAPI
# lifespan below.
_mcp_app = build_mcp_app()


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Run the FastAPI app and the MCP StreamableHTTP session manager together."""
    async with mcp.session_manager.run():
        yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

# Strict CORS allowlist (no wildcard origin). The dev Vite origin is allowed
# by default; production sets the real frontend origin(s) via CORS_ORIGINS.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

app.include_router(api_router)

# MCP server (chat bot integration). The bot pod POSTs JSON-RPC tool calls
# to /mcp with `X-Bot-Api-Key`, `X-Bot-Subject-Type`, `X-Bot-Subject-Id`
# headers. Inner StreamableHTTP route is "/" so the mount prefix strip makes
# both /mcp and /mcp/ match.
app.mount("/mcp", _mcp_app)


@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}
