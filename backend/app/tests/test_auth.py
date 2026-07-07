"""Tests for authentication (login, token issuance)."""

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.user import User


async def _create_user(
    session: AsyncSession, email: str = "user@test.com", password: str = "secret"
) -> User:
    user = User(email=email, name="Test User", password=hash_password(password))
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def test_login_success(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "user@test.com", "password": "secret"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert data["access_token"]


async def test_login_wrong_password(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "user@test.com", "password": "wrong"},
    )
    assert response.status_code == 401


async def test_login_unknown_email(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "ghost@test.com", "password": "secret"},
    )
    assert response.status_code == 401


async def _auth_headers(
    client: AsyncClient, email: str = "user@test.com", password: str = "secret"
) -> dict[str, str]:
    resp = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


async def test_me_returns_profile(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    response = await client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["user_name"] == "Test User"
    assert data["email"] == "user@test.com"


async def test_me_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


async def test_me_rejects_invalid_token(client: AsyncClient) -> None:
    headers = {"Authorization": "Bearer not.a.real.token"}
    response = await client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401
