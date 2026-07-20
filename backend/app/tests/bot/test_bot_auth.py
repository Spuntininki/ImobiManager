"""Tests for `POST /api/v1/bot/auth/validate` (machine-to-machine)."""

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.user import User

from .conftest import TEST_BOT_API_KEY  # noqa: F401 — autouse fixture


async def _create_user(
    session: AsyncSession, email: str = "user@test.com", password: str = "secret"
) -> User:
    user = User(email=email, name="Test User", password=hash_password(password))
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def _create_user_token(client: AsyncClient, headers: dict[str, str]) -> str:
    resp = await client.post("/api/v1/bot-tokens", json={"subject_type": "USER"}, headers=headers)
    return resp.json()["token"]


async def test_validate_requires_api_key(client: AsyncClient, db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    headers = await _auth_headers(client, user.email, "secret")
    token = await _create_user_token(client, headers)

    # No X-Bot-Api-Key → 401.
    resp = await client.post(
        "/api/v1/bot/auth/validate",
        json={"token": token, "chat_id": 42},
    )
    assert resp.status_code == 401

    # Wrong key → 401.
    resp = await client.post(
        "/api/v1/bot/auth/validate",
        json={"token": token, "chat_id": 42},
        headers={"X-Bot-Api-Key": "wrong"},
    )
    assert resp.status_code == 401


async def _auth_headers(client: AsyncClient, email: str, password: str) -> dict[str, str]:
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


async def test_validate_binds_chat_then_rejects_other_chat(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    user = await _create_user(db_session)
    headers = await _auth_headers(client, user.email, "secret")
    token = await _create_user_token(client, headers)

    # First call binds chat_id=100.
    r1 = await client.post(
        "/api/v1/bot/auth/validate",
        json={"token": token, "chat_id": 100},
        headers={"X-Bot-Api-Key": TEST_BOT_API_KEY},
    )
    assert r1.status_code == 200
    body = r1.json()
    assert body["subject_type"] == "USER"
    assert body["subject_id"] == user.id
    assert body["linked"] is False  # just bound

    # Same chat_id → linked=True.
    r2 = await client.post(
        "/api/v1/bot/auth/validate",
        json={"token": token, "chat_id": 100},
        headers={"X-Bot-Api-Key": TEST_BOT_API_KEY},
    )
    assert r2.status_code == 200
    assert r2.json()["linked"] is True

    # Different chat_id → 401 (token is bound to 100).
    r3 = await client.post(
        "/api/v1/bot/auth/validate",
        json={"token": token, "chat_id": 999},
        headers={"X-Bot-Api-Key": TEST_BOT_API_KEY},
    )
    assert r3.status_code == 401


async def test_validate_unknown_token_returns_401(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    resp = await client.post(
        "/api/v1/bot/auth/validate",
        json={"token": "TOTESINVALID", "chat_id": 1},
        headers={"X-Bot-Api-Key": TEST_BOT_API_KEY},
    )
    assert resp.status_code == 401


async def test_validate_rejected_after_revoke(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    user = await _create_user(db_session)
    headers = await _auth_headers(client, user.email, "secret")
    created = await client.post(
        "/api/v1/bot-tokens", json={"subject_type": "USER"}, headers=headers
    )
    token = created.json()["token"]
    token_id = created.json()["id"]

    # Bind first.
    r1 = await client.post(
        "/api/v1/bot/auth/validate",
        json={"token": token, "chat_id": 1},
        headers={"X-Bot-Api-Key": TEST_BOT_API_KEY},
    )
    assert r1.status_code == 200

    # Revoke.
    rev = await client.post(f"/api/v1/bot-tokens/{token_id}/revoke", headers=headers)
    assert rev.status_code == 200

    # After revoke → 401.
    r2 = await client.post(
        "/api/v1/bot/auth/validate",
        json={"token": token, "chat_id": 1},
        headers={"X-Bot-Api-Key": TEST_BOT_API_KEY},
    )
    assert r2.status_code == 401
