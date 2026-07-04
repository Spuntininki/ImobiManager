"""Tests for the Renter CRUD endpoints (authenticated, global scoping)."""

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


async def _auth_headers(
    client: AsyncClient, email: str = "user@test.com", password: str = "secret"
) -> dict[str, str]:
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def test_create_renter_requires_auth(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/renters",
        json={"name": "No Auth", "primary_contact": "+55 11 9999-9999"},
    )
    assert response.status_code == 401


async def test_create_renter_minimal(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    response = await client.post(
        "/api/v1/renters",
        json={"name": "Maria Souza", "primary_contact": "+55 11 9999-9999"},
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Maria Souza"
    assert data["primary_contact"] == "+55 11 9999-9999"
    assert data["secondary_contact"] is None
    assert data["email"] is None
    assert data["id"] is not None


async def test_create_renter_full(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    response = await client.post(
        "/api/v1/renters",
        json={
            "name": "João Lima",
            "primary_contact": "+55 11 9000-0000",
            "secondary_contact": "+55 11 9111-1111",
            "email": "joao@example.com",
        },
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["secondary_contact"] == "+55 11 9111-1111"
    assert data["email"] == "joao@example.com"


async def test_create_renter_missing_required_name(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    response = await client.post(
        "/api/v1/renters",
        json={"primary_contact": "+55 11 9999-9999"},
        headers=headers,
    )
    assert response.status_code == 422


async def test_create_renter_missing_required_primary_contact(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    response = await client.post(
        "/api/v1/renters",
        json={"name": "Sem Contato"},
        headers=headers,
    )
    assert response.status_code == 422


async def test_list_renters_empty(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    response = await client.get("/api/v1/renters", headers=headers)
    assert response.status_code == 200
    assert response.json() == []


async def test_list_renters(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    await client.post(
        "/api/v1/renters",
        json={"name": "Tenant A", "primary_contact": "111"},
        headers=headers,
    )
    await client.post(
        "/api/v1/renters",
        json={"name": "Tenant B", "primary_contact": "222"},
        headers=headers,
    )
    response = await client.get("/api/v1/renters", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert {r["name"] for r in data} == {"Tenant A", "Tenant B"}


async def test_get_renter_by_id_requires_auth(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    create = await client.post(
        "/api/v1/renters",
        json={"name": "Single", "primary_contact": "333"},
        headers=headers,
    )
    renter_id = create.json()["id"]
    response = await client.get(f"/api/v1/renters/{renter_id}")
    assert response.status_code == 401


async def test_get_renter_by_id(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    create = await client.post(
        "/api/v1/renters",
        json={"name": "Single", "primary_contact": "333"},
        headers=headers,
    )
    renter_id = create.json()["id"]
    response = await client.get(f"/api/v1/renters/{renter_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Single"


async def test_get_renter_not_found(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    response = await client.get("/api/v1/renters/9999", headers=headers)
    assert response.status_code == 404


async def test_update_renter(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    create = await client.post(
        "/api/v1/renters",
        json={"name": "Old", "primary_contact": "444"},
        headers=headers,
    )
    renter_id = create.json()["id"]
    response = await client.put(
        f"/api/v1/renters/{renter_id}",
        json={
            "name": "New",
            "primary_contact": "555",
            "secondary_contact": "666",
            "email": "new@example.com",
        },
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New"
    assert data["primary_contact"] == "555"
    assert data["secondary_contact"] == "666"
    assert data["email"] == "new@example.com"


async def test_update_renter_not_found(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    response = await client.put(
        "/api/v1/renters/9999",
        json={"name": "X", "primary_contact": "0"},
        headers=headers,
    )
    assert response.status_code == 404


async def test_delete_renter(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    create = await client.post(
        "/api/v1/renters",
        json={"name": "To Delete", "primary_contact": "777"},
        headers=headers,
    )
    renter_id = create.json()["id"]
    response = await client.delete(f"/api/v1/renters/{renter_id}", headers=headers)
    assert response.status_code == 204
    get = await client.get(f"/api/v1/renters/{renter_id}", headers=headers)
    assert get.status_code == 404


async def test_delete_renter_not_found(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    response = await client.delete("/api/v1/renters/9999", headers=headers)
    assert response.status_code == 404
