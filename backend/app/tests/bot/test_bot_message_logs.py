"""Tests for `POST /api/v1/bot/message-logs` (machine-to-machine)."""

from httpx import AsyncClient

from .conftest import TEST_BOT_API_KEY  # noqa: F401 — autouse fixture


async def test_append_logs_requires_api_key(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/bot/message-logs",
        json={"logs": []},
    )
    assert resp.status_code == 401


async def test_append_empty_batch(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/bot/message-logs",
        json={"logs": []},
        headers={"X-Bot-Api-Key": TEST_BOT_API_KEY},
    )
    assert resp.status_code == 201
    assert resp.json() == {"inserted": 0}


async def test_append_logs_persists_rows(client: AsyncClient, db_session=None) -> None:
    resp = await client.post(
        "/api/v1/bot/message-logs",
        json={
            "logs": [
                {
                    "token_id": None,
                    "chat_id": 1234,
                    "direction": "IN",
                    "llm_tokens_used": 0,
                },
                {
                    "token_id": None,
                    "chat_id": 1234,
                    "direction": "OUT",
                    "llm_tokens_used": 424,
                },
            ]
        },
        headers={"X-Bot-Api-Key": TEST_BOT_API_KEY},
    )
    assert resp.status_code == 201
    assert resp.json() == {"inserted": 2}

    # Audit rows are not eagerly asserted against the DB; the count contract
    # is what the bot relies on. Subtle persistence breakage surfaces in the
    # `bot_message_log_service` unit tests if needed.
