"""ImobiManager bot entrypoint.

Starts the Telegram long-polling loop, opens the shared `httpx.AsyncClient`
used by the auth + log clients, spins up the periodic log flush, and waits
for SIGINT/SIGTERM.

Run locally:
    uv run python -m app.main
"""

from __future__ import annotations

import logging

import httpx
import uvloop

from app.llm.agent import AgentRunner
from app.logging.message_log_publisher import MessageLogPublisher
from app.platforms.telegram.client import TelegramClient
from app.platforms.telegram.poller import run_polling
from app.router import MessageRouter
from app.security.rate_limit import RateLimiter
from app.security.token_auth import ChatSessionStore, TokenAuthenticator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    # Single httpx client reused by everything that talks to the backend
    # (auth, log publisher) and by Telegram.
    http = httpx.AsyncClient(timeout=httpx.Timeout(60.0))

    tg = TelegramClient(http=http)
    me = await tg.get_me()
    logger.info("Telegram bot online as @%s (id=%s)", me.get("username"), me.get("id"))

    auth = TokenAuthenticator(http=http)
    limiter = RateLimiter()
    agent = AgentRunner()
    sessions = ChatSessionStore()
    log_publisher = MessageLogPublisher(http=http)
    await log_publisher.start()

    router = MessageRouter(
        auth=auth,
        limiter=limiter,
        agent_runner=agent,
        log_publisher=log_publisher,
        sessions=sessions,
    )

    try:
        await run_polling(tg, router)
    finally:
        await log_publisher.stop()
        await tg.aclose()
        # We own `http` here; closing it after the clients that use it.
        await http.aclose()
    logger.info("bot stopped")


def run() -> None:
    uvloop.run(main())


if __name__ == "__main__":
    run()
