"""End-to-end router test with fake Telegram + auth backend.

Covers:
- unauthenticated message → onboarding reply, no LLM call.
- unknown token → onboarding reply (no reconnaissance).
- valid token + LLM mocking → rate limit / throttle path.
- per-token lock: second concurrent message dropped.

We do NOT instantiate the LangChain agent here: it would require an
OpenRouter API key and a live backend MCP server. The router accepts a
duck-typed `agent_runner` with `async def run(...)`.
"""

import asyncio

import httpx
import pytest

from app.logging.message_log_publisher import MessageLogPublisher
from app.platforms.telegram.types import InboundMessage
from app.router import ONBOARDING_TEXT, RATE_LIMIT_TEXT, MessageRouter
from app.security.rate_limit import RateLimiter
from app.security.token_auth import AuthResult, TokenAuthenticator


class FakeTelegram:
    """Captures outbound send_message calls instead of hitting Telegram."""

    def __init__(self) -> None:
        self.sent: list[tuple[int, str]] = []

    async def send_message(self, chat_id: int, text: str) -> None:
        self.sent.append((chat_id, text))


class FakeAuth(TokenAuthenticator):
    """Skips HTTP entirely; uses a preconfigured dict."""

    def __init__(self, table: dict[str, AuthResult]) -> None:
        # Bypass __init__ which needs an httpx client — we override validate.
        self._table = table

    async def validate(self, token: str, chat_id: int) -> AuthResult | None:
        return self._table.get(token)


class FakeAgent:
    """Records runs and returns a fixed reply."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, int, int]] = []

    async def run(
        self,
        *,
        chat_id: int,
        user_text: str,
        subject_type: str,
        subject_id: int,
    ) -> str:
        self.calls.append((subject_type, subject_id, chat_id))
        return f"reply:{user_text}"


@pytest.fixture
def http_for_logs() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        transport=httpx.MockTransport(lambda req: httpx.Response(201, json={"inserted": 0}))
    )


async def test_unauthenticated_sends_onboarding(
    http_for_logs: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.config import settings

    monkeypatch.setattr(settings, "bot_mcp_api_key", "test")
    monkeypatch.setattr(settings, "bot_rate_limit_user_per_min", 99)
    monkeypatch.setattr(settings, "bot_rate_limit_chat_per_min", 99)

    tg = FakeTelegram()
    auth = FakeAuth({})
    limiter = RateLimiter()
    agent = FakeAgent()
    logs = MessageLogPublisher(http=http_for_logs)

    router = MessageRouter(auth=auth, limiter=limiter, agent_runner=agent, log_publisher=logs)
    await router.route(InboundMessage(update_id=1, chat_id=10, text="ola"), tg)

    assert tg.sent == [(10, ONBOARDING_TEXT)]
    assert agent.calls == []


async def test_unknown_token_replies_onboarding_only(
    http_for_logs: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.config import settings

    monkeypatch.setattr(settings, "bot_mcp_api_key", "test")
    monkeypatch.setattr(settings, "bot_rate_limit_user_per_min", 99)
    monkeypatch.setattr(settings, "bot_rate_limit_chat_per_min", 99)

    tg = FakeTelegram()
    auth = FakeAuth({})
    limiter = RateLimiter()
    agent = FakeAgent()
    logs = MessageLogPublisher(http=http_for_logs)

    router = MessageRouter(auth=auth, limiter=limiter, agent_runner=agent, log_publisher=logs)
    await router.route(InboundMessage(update_id=1, chat_id=10, text="BADTOKEN listar"), tg)

    # Unknown token → same onboarding reply (no reconnaissance).
    assert tg.sent == [(10, ONBOARDING_TEXT)]
    assert agent.calls == []


async def test_valid_token_runs_agent_and_replies(
    http_for_logs: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.config import settings

    monkeypatch.setattr(settings, "bot_mcp_api_key", "test")
    monkeypatch.setattr(settings, "bot_rate_limit_user_per_min", 99)
    monkeypatch.setattr(settings, "bot_rate_limit_chat_per_min", 99)

    tg = FakeTelegram()
    auth = FakeAuth(
        {
            "GOOD": AuthResult(
                token_id=1,
                subject_type="USER",
                subject_id=5,
                status="ACTIVE",
                expires_at=None,
                linked=True,
            )
        }
    )
    limiter = RateLimiter()
    agent = FakeAgent()
    logs = MessageLogPublisher(http=http_for_logs)

    router = MessageRouter(auth=auth, limiter=limiter, agent_runner=agent, log_publisher=logs)
    await router.route(InboundMessage(update_id=1, chat_id=10, text="GOOD quantos imoveis?"), tg)

    assert agent.calls == [("USER", 5, 10)]
    assert tg.sent == [(10, "reply:quantos imoveis?")]


async def test_rate_limit_reject_sends_throttle_reply_once(
    http_for_logs: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.config import settings

    monkeypatch.setattr(settings, "bot_mcp_api_key", "test")
    monkeypatch.setattr(settings, "bot_rate_limit_user_per_min", 1)
    monkeypatch.setattr(settings, "bot_rate_limit_user_per_day", 99)
    monkeypatch.setattr(settings, "bot_rate_limit_chat_per_min", 99)

    tg = FakeTelegram()
    auth = FakeAuth(
        {
            "RATED": AuthResult(
                token_id=9,
                subject_type="USER",
                subject_id=5,
                status="ACTIVE",
                expires_at=None,
                linked=True,
            )
        }
    )
    limiter = RateLimiter()
    agent = FakeAgent()
    logs = MessageLogPublisher(http=http_for_logs)

    router = MessageRouter(auth=auth, limiter=limiter, agent_runner=agent, log_publisher=logs)

    # First call allowed, runs the agent.
    await router.route(InboundMessage(update_id=1, chat_id=10, text="RATED pergunta 1"), tg)
    assert agent.calls == [("USER", 5, 10)]

    # Second call within minute → throttle reply.
    await router.route(InboundMessage(update_id=2, chat_id=10, text="RATED pergunta 2"), tg)
    assert RATE_LIMIT_TEXT in [text for _, text in tg.sent]

    # Third call within cooldown → no extra throttle reply.
    sent_before = len(tg.sent)
    await router.route(InboundMessage(update_id=3, chat_id=10, text="RATED pergunta 3"), tg)
    assert len(tg.sent) == sent_before  # no new reply


async def test_per_token_lock_drops_concurrent_duplicate(
    http_for_logs: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.config import settings

    monkeypatch.setattr(settings, "bot_mcp_api_key", "test")
    monkeypatch.setattr(settings, "bot_rate_limit_user_per_min", 99)
    monkeypatch.setattr(settings, "bot_rate_limit_chat_per_min", 99)

    tg = FakeTelegram()
    auth = FakeAuth(
        {
            "T": AuthResult(
                token_id=1,
                subject_type="USER",
                subject_id=5,
                status="ACTIVE",
                expires_at=None,
                linked=True,
            )
        }
    )
    limiter = RateLimiter()
    agent_calls_started = asyncio.Event()
    agent_calls_done = asyncio.Event()

    class SlowAgent:
        async def run(self, *, chat_id, user_text, subject_type, subject_id):
            agent_calls_started.set()
            await asyncio.sleep(0.05)
            agent_calls_done.set()
            return "slow-reply"

    logs = MessageLogPublisher(http=http_for_logs)
    router = MessageRouter(auth=auth, limiter=limiter, agent_runner=SlowAgent(), log_publisher=logs)

    # Two messages for the same token arrive concurrently. The router fires
    # them as separate tasks (like `run_polling` does).
    t1 = asyncio.create_task(
        router.route(InboundMessage(update_id=1, chat_id=10, text="T msg a"), tg)
    )
    t2 = asyncio.create_task(
        router.route(InboundMessage(update_id=2, chat_id=10, text="T msg b"), tg)
    )
    await asyncio.gather(t1, t2)

    # Only one of the two reached the agent; the other was dropped by the
    # per-token lock.
    assert agent_calls_started.is_set()
    assert agent_calls_done.is_set()
    # Exactly one agent-driven reply (the other was silently dropped).
    assert [text for _, text in tg.sent if text == "slow-reply"].count("slow-reply") == 1
