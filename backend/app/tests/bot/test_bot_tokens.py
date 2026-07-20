"""Tests for admin bot-token endpoints (`/api/v1/bot-tokens`)."""

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


async def _auth_headers(client: AsyncClient, email: str, password: str) -> dict[str, str]:
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


async def test_create_user_token_returns_plain_value_once(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    user = await _create_user(db_session)
    headers = await _auth_headers(client, user.email, "secret")

    resp = await client.post(
        "/api/v1/bot-tokens",
        json={"subject_type": "USER"},
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["subject_type"] == "USER"
    assert data["subject_id"] == user.id
    assert data["status"] == "ACTIVE"
    assert data["chat_id"] is None
    assert data["token"]  # plain token returned on creation
    plain = data["token"]

    # Listing redacts the token.
    listing = await client.get("/api/v1/bot-tokens", headers=headers)
    assert listing.status_code == 200
    rows = listing.json()
    assert len(rows) == 1
    assert rows[0]["id"] == data["id"]
    assert rows[0]["token"] is None  # redacted


async def test_create_renter_token_requires_renter_within_user_owners(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    user = await _create_user(db_session)
    headers = await _auth_headers(client, user.email, "secret")

    # Create one owner (auto-linked to the user) and a renter on it.
    owner_resp = await client.post("/api/v1/owners", json={"name": "Imob One"}, headers=headers)
    owner_id = owner_resp.json()["id"]
    renter_resp = await client.post(
        f"/api/v1/owners/{owner_id}/renters",
        json={"name": "Maria", "primary_contact": "+55 11 99999-0000"},
        headers=headers,
    )
    renter_id = renter_resp.json()["id"]

    # Missing renter_id → 422.
    bad = await client.post(
        "/api/v1/bot-tokens",
        json={"subject_type": "RENTER"},
        headers=headers,
    )
    assert bad.status_code == 422

    # RENTER outside any owner managed by this user → 404.
    from app.models.renter import Renter

    stranger = Renter(name="Stranger", primary_contact="+55 11 1111-1111")
    db_session.add(stranger)
    await db_session.commit()
    forbidden = await client.post(
        "/api/v1/bot-tokens",
        json={"subject_type": "RENTER", "renter_id": stranger.id},
        headers=headers,
    )
    assert forbidden.status_code == 404

    # Valid renter → 201.
    ok = await client.post(
        "/api/v1/bot-tokens",
        json={"subject_type": "RENTER", "renter_id": renter_id},
        headers=headers,
    )
    assert ok.status_code == 201
    payload = ok.json()
    assert payload["subject_type"] == "RENTER"
    assert payload["subject_id"] == renter_id


async def test_revoke_token(client: AsyncClient, db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    headers = await _auth_headers(client, user.email, "secret")
    created = await client.post(
        "/api/v1/bot-tokens", json={"subject_type": "USER"}, headers=headers
    )
    token_id = created.json()["id"]

    revoke = await client.post(f"/api/v1/bot-tokens/{token_id}/revoke", headers=headers)
    assert revoke.status_code == 200
    assert revoke.json()["status"] == "REVOKED"

    # Revoking an unknown id → 404.
    missing = await client.post("/api/v1/bot-tokens/99999/revoke", headers=headers)
    assert missing.status_code == 404


async def test_tokens_require_authentication(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/bot-tokens")
    assert resp.status_code == 401
