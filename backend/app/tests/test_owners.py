"""Tests for the Owner CRUD endpoints (authenticated + scoped via user_owners)."""

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


async def _auth_token(
    client: AsyncClient, email: str = "user@test.com", password: str = "secret"
) -> str:
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return resp.json()["access_token"]


async def _auth_headers(
    client: AsyncClient, email: str = "user@test.com", password: str = "secret"
) -> dict[str, str]:
    token = await _auth_token(client, email, password)
    return {"Authorization": f"Bearer {token}"}


async def test_create_owner_requires_auth(client: AsyncClient) -> None:
    response = await client.post("/api/v1/owners", json={"name": "No Auth"})
    assert response.status_code == 401


async def test_create_owner(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    response = await client.post("/api/v1/owners", json={"name": "João Silva"}, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "João Silva"
    assert data["id"] is not None


async def test_list_owners_empty(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    response = await client.get("/api/v1/owners", headers=headers)
    assert response.status_code == 200
    assert response.json() == []


async def test_list_owners_only_returns_linked(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    user = await _create_user(db_session)
    headers = await _auth_headers(client)
    # Create two owners for this user
    await client.post("/api/v1/owners", json={"name": "Mine A"}, headers=headers)
    await client.post("/api/v1/owners", json={"name": "Mine B"}, headers=headers)
    # Create an owner NOT linked to this user
    from app.models.owner import Owner

    other = Owner(name="Someone Elses")
    db_session.add(other)
    await db_session.commit()
    response = await client.get("/api/v1/owners", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert {o["name"] for o in data} == {"Mine A", "Mine B"}


async def test_get_owner_by_id_requires_auth(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    create = await client.post("/api/v1/owners", json={"name": "Single"}, headers=headers)
    owner_id = create.json()["id"]
    response = await client.get(f"/api/v1/owners/{owner_id}")
    assert response.status_code == 401


async def test_get_owner_by_id(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    create = await client.post("/api/v1/owners", json={"name": "Single"}, headers=headers)
    owner_id = create.json()["id"]
    response = await client.get(f"/api/v1/owners/{owner_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Single"


async def test_get_owner_forbidden_when_not_linked(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    user = await _create_user(db_session)
    headers = await _auth_headers(client)
    # An owner the user did NOT create
    from app.models.owner import Owner

    other = Owner(name="Forbidden")
    db_session.add(other)
    await db_session.commit()
    response = await client.get(f"/api/v1/owners/{other.id}", headers=headers)
    assert response.status_code == 403


async def test_update_owner(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    create = await client.post("/api/v1/owners", json={"name": "Old"}, headers=headers)
    owner_id = create.json()["id"]
    response = await client.put(f"/api/v1/owners/{owner_id}", json={"name": "New"}, headers=headers)
    assert response.status_code == 200
    assert response.json()["name"] == "New"


async def test_update_owner_forbidden_when_not_linked(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    from app.models.owner import Owner

    other = Owner(name="Forbidden")
    db_session.add(other)
    await db_session.commit()
    response = await client.put(f"/api/v1/owners/{other.id}", json={"name": "X"}, headers=headers)
    assert response.status_code == 403


async def test_delete_owner(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    create = await client.post("/api/v1/owners", json={"name": "To Delete"}, headers=headers)
    owner_id = create.json()["id"]
    response = await client.delete(f"/api/v1/owners/{owner_id}", headers=headers)
    assert response.status_code == 204
    get = await client.get(f"/api/v1/owners/{owner_id}", headers=headers)
    assert get.status_code == 404


async def test_delete_owner_forbidden_when_not_linked(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    from app.models.owner import Owner

    other = Owner(name="Forbidden")
    db_session.add(other)
    await db_session.commit()
    response = await client.delete(f"/api/v1/owners/{other.id}", headers=headers)
    assert response.status_code == 403
