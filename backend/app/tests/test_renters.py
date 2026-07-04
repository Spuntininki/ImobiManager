"""Tests for the Renter CRUD endpoints (owner-scoped via owner_renters)."""

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.owner import Owner
from app.models.renter import Renter
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


async def _create_owner_via_api(
    client: AsyncClient, headers: dict[str, str], name: str = "Owner One"
) -> int:
    resp = await client.post("/api/v1/owners", json={"name": name}, headers=headers)
    return resp.json()["id"]


async def _create_renter_via_api(
    client: AsyncClient,
    headers: dict[str, str],
    owner_id: int,
    name: str = "Maria Souza",
    primary_contact: str = "+55 11 9999-9999",
) -> int:
    resp = await client.post(
        f"/api/v1/owners/{owner_id}/renters",
        json={"name": name, "primary_contact": primary_contact},
        headers=headers,
    )
    return resp.json()["id"]


# --- Auth required ---


async def test_create_renter_requires_auth(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/owners/1/renters",
        json={"name": "No Auth", "primary_contact": "+55 11 9999-9999"},
    )
    assert response.status_code == 401


async def test_list_renters_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/owners/1/renters")
    assert response.status_code == 401


async def test_get_renter_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/renters/1")
    assert response.status_code == 401


# --- Create ---


async def test_create_renter_minimal(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    owner_id = await _create_owner_via_api(client, headers)
    response = await client.post(
        f"/api/v1/owners/{owner_id}/renters",
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
    owner_id = await _create_owner_via_api(client, headers)
    response = await client.post(
        f"/api/v1/owners/{owner_id}/renters",
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
    owner_id = await _create_owner_via_api(client, headers)
    response = await client.post(
        f"/api/v1/owners/{owner_id}/renters",
        json={"primary_contact": "+55 11 9999-9999"},
        headers=headers,
    )
    assert response.status_code == 422


async def test_create_renter_missing_required_primary_contact(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    owner_id = await _create_owner_via_api(client, headers)
    response = await client.post(
        f"/api/v1/owners/{owner_id}/renters",
        json={"name": "Sem Contato"},
        headers=headers,
    )
    assert response.status_code == 422


async def test_create_renter_for_owner_not_managed_returns_404(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """User must manage the owner to create a renter under it (404, not 403)."""
    await _create_user(db_session)
    headers = await _auth_headers(client)
    # Owner NOT linked to this user
    other = Owner(name="Someone Elses")
    db_session.add(other)
    await db_session.commit()
    response = await client.post(
        f"/api/v1/owners/{other.id}/renters",
        json={"name": "X", "primary_contact": "0"},
        headers=headers,
    )
    assert response.status_code == 404


# --- List ---


async def test_list_renters_empty(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    owner_id = await _create_owner_via_api(client, headers)
    response = await client.get(f"/api/v1/owners/{owner_id}/renters", headers=headers)
    assert response.status_code == 200
    assert response.json() == []


async def test_list_renters_for_owner(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    owner_id = await _create_owner_via_api(client, headers)
    await _create_renter_via_api(client, headers, owner_id, name="Tenant A")
    await _create_renter_via_api(client, headers, owner_id, name="Tenant B")
    response = await client.get(f"/api/v1/owners/{owner_id}/renters", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert {r["name"] for r in data} == {"Tenant A", "Tenant B"}


async def test_list_renters_scoped_to_owner(client: AsyncClient, db_session: AsyncSession) -> None:
    """Renters linked to owner B do not appear under owner A."""
    await _create_user(db_session)
    headers = await _auth_headers(client)
    owner_a = await _create_owner_via_api(client, headers, name="Owner A")
    owner_b = await _create_owner_via_api(client, headers, name="Owner B")
    await _create_renter_via_api(client, headers, owner_a, name="Tenant A1")
    await _create_renter_via_api(client, headers, owner_b, name="Tenant B1")
    response = await client.get(f"/api/v1/owners/{owner_a}/renters", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Tenant A1"


async def test_list_renters_for_owner_not_managed_returns_404(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    other = Owner(name="Someone Elses")
    db_session.add(other)
    await db_session.commit()
    response = await client.get(f"/api/v1/owners/{other.id}/renters", headers=headers)
    assert response.status_code == 404


# --- Get by id ---


async def test_get_renter_by_id(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    owner_id = await _create_owner_via_api(client, headers)
    renter_id = await _create_renter_via_api(client, headers, owner_id, name="Single")
    response = await client.get(f"/api/v1/renters/{renter_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Single"


async def test_get_renter_not_found(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    response = await client.get("/api/v1/renters/9999", headers=headers)
    assert response.status_code == 404


async def test_get_renter_not_linked_to_managed_owner_returns_404(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Renter exists but linked only to an owner the user does NOT manage → 404."""
    await _create_user(db_session)
    headers = await _auth_headers(client)
    # Create a renter NOT linked to any owner the user manages
    other_renter = Renter(name="Hidden", primary_contact="123")
    db_session.add(other_renter)
    await db_session.commit()
    response = await client.get(f"/api/v1/renters/{other_renter.id}", headers=headers)
    assert response.status_code == 404


# --- Update ---


async def test_update_renter(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    owner_id = await _create_owner_via_api(client, headers)
    renter_id = await _create_renter_via_api(client, headers, owner_id, name="Old")
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


async def test_update_renter_not_linked_to_managed_owner_returns_404(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    other_renter = Renter(name="Hidden", primary_contact="123")
    db_session.add(other_renter)
    await db_session.commit()
    response = await client.put(
        f"/api/v1/renters/{other_renter.id}",
        json={"name": "X", "primary_contact": "0"},
        headers=headers,
    )
    assert response.status_code == 404


# --- Delete ---


async def test_delete_renter(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    owner_id = await _create_owner_via_api(client, headers)
    renter_id = await _create_renter_via_api(client, headers, owner_id, name="To Delete")
    response = await client.delete(f"/api/v1/renters/{renter_id}", headers=headers)
    assert response.status_code == 204
    get = await client.get(f"/api/v1/renters/{renter_id}", headers=headers)
    assert get.status_code == 404


async def test_delete_renter_not_found(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    response = await client.delete("/api/v1/renters/9999", headers=headers)
    assert response.status_code == 404


async def test_delete_renter_not_linked_to_managed_owner_returns_404(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    other_renter = Renter(name="Hidden", primary_contact="123")
    db_session.add(other_renter)
    await db_session.commit()
    response = await client.delete(f"/api/v1/renters/{other_renter.id}", headers=headers)
    assert response.status_code == 404
