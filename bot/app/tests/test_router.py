"""End-to-end router test with fake Telegram + auth backend.

Covers:
- unauthenticated message → onboarding reply, no LLM call.
- unknown token → onboarding reply (no reconnaissance).
- valid token + LLM mocking → rate limit / throttle path.
- per-token lock: second concurrent message dropped.
- session persistence after `/start`.
- `/logout` clears the session.
- revoked token during an active session clears it.
- `/help` command.
- `/start` with no token when already linked → already-linked reply.

We do NOT instantiate the LangChain agent here: it would require an
OpenRouter API key and a live backend MCP server. The router accepts a
duck-typed `agent_runner` with `async def run(...)`.
"""

import asyncio

import httpx
import pytest

from app.logging.message_log_publisher import MessageLogPublisher
from app.platforms.telegram.types import InboundMessage
from app.router import (
    ALREADY_LINKED_TEXT,
    HELP_TEXT,
    LINKED_TEXT,
    LOGOUT_TEXT,
    ONBOARDING_TEXT,
    RATE_LIMIT_TEXT,
    MessageRouter,
)
from app.security.rate_limit import RateLimiter
from app.security.token_auth import AuthResult, ChatSessionStore, TokenAuthenticator


class FakeTelegram:
    """Captures outbound send_message calls instead of hitting Telegram."""

    def __init__(self) -> None:
        self.sent: list[tuple[int, str]] = []

    async def send_message(self, chat_id: int, text: str) -> None:
        self.sent.append((chat_id, text))


class FakeAuth(TokenAuthenticator):
    """Skips HTTP entirely; uses a preconfigured dict.

    Supports toggling tokens to None mid-test (simulating revocation).
    """

    def __init__(self, table: dict[str, AuthResult]) -> None:
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


def _make_auth_result(token_id: int = 1) -> AuthResult:
    return AuthResult(
        token_id=token_id,
        subject_type="USER",
        subject_id=5,
        status="ACTIVE",
        expires_at=None,
        linked=True,
    )


def _make_router(
    *,
    auth: FakeAuth,
    tg: FakeTelegram,
    http_for_logs: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    agent: FakeAgent | None = None,
    sessions: ChatSessionStore | None = None,
) -> tuple[MessageRouter, ChatSessionStore]:
    from app.config import settings

    monkeypatch.setattr(settings, "bot_mcp_api_key", "test")
    monkeypatch.setattr(settings, "bot_rate_limit_user_per_min", 99)
    monkeypatch.setattr(settings, "bot_rate_limit_user_per_day", 99)
    monkeypatch.setattr(settings, "bot_rate_limit_chat_per_min", 99)
    limiter = RateLimiter()
    ag = agent or FakeAgent()
    ss = sessions or ChatSessionStore()
    logs = MessageLogPublisher(http=http_for_logs)
    router = MessageRouter(
        auth=auth, limiter=limiter, agent_runner=ag, log_publisher=logs, sessions=ss
    )
    return router, ss


# --- No command, no session: onboarding -------------------------------


async def test_unauthenticated_sends_onboarding(
    http_for_logs: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    tg = FakeTelegram()
    auth = FakeAuth({})
    router, _ = _make_router(auth=auth, tg=tg, http_for_logs=http_for_logs, monkeypatch=monkeypatch)
    await router.route(InboundMessage(update_id=1, chat_id=10, text="ola"), tg)
    assert tg.sent == [(10, ONBOARDING_TEXT)]


async def test_unknown_token_replies_onboarding_only(
    http_for_logs: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    tg = FakeTelegram()
    auth = FakeAuth({})
    router, _ = _make_router(auth=auth, tg=tg, http_for_logs=http_for_logs, monkeypatch=monkeypatch)
    await router.route(InboundMessage(update_id=1, chat_id=10, text="BADTOKEN listar"), tg)
    assert tg.sent == [(10, ONBOARDING_TEXT)]


# --- /start <TOKEN> persists session ----------------------------------


async def test_start_binds_session_then_question_without_token_works(
    http_for_logs: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    tg = FakeTelegram()
    auth = FakeAuth({"GOOD": _make_auth_result()})
    agent = FakeAgent()
    router, sessions = _make_router(
        auth=auth, tg=tg, http_for_logs=http_for_logs, monkeypatch=monkeypatch, agent=agent
    )

    # /start GOOD (no body) → linked confirmation, no agent call.
    await router.route(InboundMessage(update_id=1, chat_id=10, text="/start GOOD"), tg)
    assert tg.sent[-1] == (10, LINKED_TEXT)
    assert agent.calls == []
    assert sessions.get(10) == "GOOD"

    # Follow-up question without token prefix → uses cached session.
    await router.route(InboundMessage(update_id=2, chat_id=10, text="quantos imoveis?"), tg)
    assert agent.calls == [("USER", 5, 10)]
    assert tg.sent[-1] == (10, "reply:quantos imoveis?")


async def test_start_token_with_question_runs_agent(
    http_for_logs: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    tg = FakeTelegram()
    auth = FakeAuth({"GOOD": _make_auth_result()})
    agent = FakeAgent()
    router, sessions = _make_router(
        auth=auth, tg=tg, http_for_logs=http_for_logs, monkeypatch=monkeypatch, agent=agent
    )

    await router.route(
        InboundMessage(update_id=1, chat_id=10, text="/start GOOD quantos imoveis?"), tg
    )
    assert agent.calls == [("USER", 5, 10)]
    assert tg.sent[-1] == (10, "reply:quantos imoveis?")
    assert sessions.get(10) == "GOOD"


async def test_start_without_token_when_linked_says_already(
    http_for_logs: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    tg = FakeTelegram()
    auth = FakeAuth({"GOOD": _make_auth_result()})
    agent = FakeAgent()
    sessions = ChatSessionStore()
    sessions.set(10, "GOOD")
    router, _ = _make_router(
        auth=auth,
        tg=tg,
        http_for_logs=http_for_logs,
        monkeypatch=monkeypatch,
        agent=agent,
        sessions=sessions,
    )
    await router.route(InboundMessage(update_id=1, chat_id=10, text="/start"), tg)
    assert tg.sent[-1] == (10, ALREADY_LINKED_TEXT)
    assert agent.calls == []


async def test_start_without_token_when_unlinked_sends_onboarding(
    http_for_logs: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    tg = FakeTelegram()
    auth = FakeAuth({})
    agent = FakeAgent()
    router, _ = _make_router(
        auth=auth, tg=tg, http_for_logs=http_for_logs, monkeypatch=monkeypatch, agent=agent
    )
    await router.route(InboundMessage(update_id=1, chat_id=10, text="/start"), tg)
    assert tg.sent[-1] == (10, ONBOARDING_TEXT)
    assert agent.calls == []


# --- Token-prefix path (no /start, no session) -----------------------


async def test_valid_token_prefix_runs_agent(
    http_for_logs: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    tg = FakeTelegram()
    auth = FakeAuth({"GOOD": _make_auth_result()})
    agent = FakeAgent()
    router, sessions = _make_router(
        auth=auth, tg=tg, http_for_logs=http_for_logs, monkeypatch=monkeypatch, agent=agent
    )
    await router.route(InboundMessage(update_id=1, chat_id=10, text="GOOD quantos imoveis?"), tg)
    assert agent.calls == [("USER", 5, 10)]
    assert tg.sent[-1] == (10, "reply:quantos imoveis?")
    assert sessions.get(10) == "GOOD"  # session stored for next messages


# --- /logout clears session ------------------------------------------


async def test_logout_clears_session(
    http_for_logs: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    tg = FakeTelegram()
    auth = FakeAuth({"GOOD": _make_auth_result()})
    agent = FakeAgent()
    sessions = ChatSessionStore()
    sessions.set(10, "GOOD")
    router, _ = _make_router(
        auth=auth,
        tg=tg,
        http_for_logs=http_for_logs,
        monkeypatch=monkeypatch,
        agent=agent,
        sessions=sessions,
    )

    await router.route(InboundMessage(update_id=1, chat_id=10, text="/logout"), tg)
    assert tg.sent[-1] == (10, LOGOUT_TEXT)
    assert sessions.get(10) is None

    # Follow-up question without token → onboarding (no session).
    await router.route(InboundMessage(update_id=2, chat_id=10, text="ola"), tg)
    assert tg.sent[-1] == (10, ONBOARDING_TEXT)
    assert agent.calls == []


# --- /help command ---------------------------------------------------


async def test_help_command(
    http_for_logs: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    tg = FakeTelegram()
    auth = FakeAuth({})
    agent = FakeAgent()
    router, _ = _make_router(
        auth=auth, tg=tg, http_for_logs=http_for_logs, monkeypatch=monkeypatch, agent=agent
    )
    await router.route(InboundMessage(update_id=1, chat_id=10, text="/help"), tg)
    assert tg.sent[-1] == (10, HELP_TEXT)
    assert agent.calls == []


# --- Revoked token during active session -----------------------------


async def test_revoked_token_clears_session(
    http_for_logs: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    tg = FakeTelegram()
    auth = FakeAuth({"GOOD": _make_auth_result()})
    agent = FakeAgent()
    sessions = ChatSessionStore()
    sessions.set(10, "GOOD")
    router, _ = _make_router(
        auth=auth,
        tg=tg,
        http_for_logs=http_for_logs,
        monkeypatch=monkeypatch,
        agent=agent,
        sessions=sessions,
    )

    # First message uses cached session → OK.
    await router.route(InboundMessage(update_id=1, chat_id=10, text="ola"), tg)
    assert agent.calls == [("USER", 5, 10)]

    # Revoke the token.
    auth._table = {}
    # Same chat sends another message → validate returns None → onboarding
    # and session cleared.
    await router.route(InboundMessage(update_id=2, chat_id=10, text="de novo"), tg)
    assert tg.sent[-1] == (10, ONBOARDING_TEXT)
    assert sessions.get(10) is None


# --- Rate limit (hard reject) ----------------------------------------


async def test_rate_limit_reject_sends_throttle_reply_once(
    http_for_logs: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.config import settings

    monkeypatch.setattr(settings, "bot_mcp_api_key", "test")
    monkeypatch.setattr(settings, "bot_rate_limit_user_per_min", 1)
    monkeypatch.setattr(settings, "bot_rate_limit_user_per_day", 99)
    monkeypatch.setattr(settings, "bot_rate_limit_chat_per_min", 99)

    tg = FakeTelegram()
    auth = FakeAuth({"RATED": _make_auth_result(token_id=9)})
    agent = FakeAgent()
    sessions = ChatSessionStore()
    limiter = RateLimiter()
    logs = MessageLogPublisher(http=http_for_logs)
    router = MessageRouter(
        auth=auth, limiter=limiter, agent_runner=agent, log_publisher=logs, sessions=sessions
    )

    # Pre-bind session so we can send bare text.
    sessions.set(10, "RATED")

    # First call allowed, runs the agent.
    await router.route(InboundMessage(update_id=1, chat_id=10, text="pergunta 1"), tg)
    assert agent.calls == [("USER", 5, 10)]

    # Second call within minute → throttle reply.
    await router.route(InboundMessage(update_id=2, chat_id=10, text="pergunta 2"), tg)
    assert RATE_LIMIT_TEXT in [text for _, text in tg.sent]

    # Third call within cooldown → no extra throttle reply.
    sent_before = len(tg.sent)
    await router.route(InboundMessage(update_id=3, chat_id=10, text="pergunta 3"), tg)
    assert len(tg.sent) == sent_before  # no new reply


# --- Per-token lock drops concurrent duplicates ----------------------


async def test_per_token_lock_drops_concurrent_duplicate(
    http_for_logs: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    tg = FakeTelegram()
    auth = FakeAuth({"T": _make_auth_result()})
    limiter = RateLimiter()
    agent_calls_started = asyncio.Event()
    agent_calls_done = asyncio.Event()

    class SlowAgent:
        async def run(self, *, chat_id, user_text, subject_type, subject_id):
            agent_calls_started.set()
            await asyncio.sleep(0.05)
            agent_calls_done.set()
            return "slow-reply"

    sessions = ChatSessionStore()
    # Pre-bind so both messages use the same token without prefix.
    sessions.set(10, "T")
    logs = MessageLogPublisher(http=http_for_logs)
    router = MessageRouter(
        auth=auth, limiter=limiter, agent_runner=SlowAgent(), log_publisher=logs, sessions=sessions
    )

    t1 = asyncio.create_task(
        router.route(InboundMessage(update_id=1, chat_id=10, text="msg a"), tg)
    )
    t2 = asyncio.create_task(
        router.route(InboundMessage(update_id=2, chat_id=10, text="msg b"), tg)
    )
    await asyncio.gather(t1, t2)

    assert agent_calls_started.is_set()
    assert agent_calls_done.is_set()
    assert [text for _, text in tg.sent if text == "slow-reply"].count("slow-reply") == 1
