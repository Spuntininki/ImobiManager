"""Fixtures specific to the chat bot integration tests.

Most tests use the shared `client` + `db_session` fixtures from
`app/tests/conftest.py`. Here we expose a stable `BOT_MCP_API_KEY` value via
monkeypatch (so tests don't depend on whatever `.env` happens to contain).
"""

from collections.abc import Iterator

import pytest

TEST_BOT_API_KEY = "test-bot-api-key-xyz"


@pytest.fixture(autouse=True)
def _stub_bot_api_key(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Force a known `BOT_MCP_API_KEY` for the duration of each test."""
    from app.core.config import settings

    monkeypatch.setattr(settings, "bot_mcp_api_key", TEST_BOT_API_KEY)
    yield


@pytest.fixture
def bot_api_headers() -> dict[str, str]:
    """Headers the bot pod sends on machine-to-machine calls."""
    return {"X-Bot-Api-Key": TEST_BOT_API_KEY}
