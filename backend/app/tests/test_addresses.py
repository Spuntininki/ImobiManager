"""Tests for the Address CRUD endpoints (owner-scoped, 404-only)."""

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.address import Address
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


def _valid_address_payload(**overrides: str) -> dict[str, str]:
    payload = {
        "street_name": "Rua das Flores",
        "number": "123",
        "complement": "Apto 101",
        "neighborhood": "Centro",
        "city": "São Paulo",
        "state": "SP",
        "zip_code": "01000-000",
        "type": "HOUSE",
    }
    payload.update(overrides)
    return payload


async def _create_address_via_api(
    client: AsyncClient,
    headers: dict[str, str],
    owner_id: int,
    **overrides: str,
) -> int:
    resp = await client.post(
        f"/api/v1/owners/{owner_id}/addresses",
        json=_valid_address_payload(**overrides),
        headers=headers,
    )
    return resp.json()["id"]


# --- Auth required ---


async def test_create_address_requires_auth(client: AsyncClient) -> None:
    response = await client.post("/api/v1/owners/1/addresses", json=_valid_address_payload())
    assert response.status_code == 401


async def test_list_addresses_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/owners/1/addresses")
    assert response.status_code == 401


async def test_get_address_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/addresses/1")
    assert response.status_code == 401


# --- Create ---


async def test_create_address_house(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    owner_id = await _create_owner_via_api(client, headers)
    response = await client.post(
        f"/api/v1/owners/{owner_id}/addresses",
        json=_valid_address_payload(type="HOUSE"),
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["owner_id"] == owner_id
    assert data["street_name"] == "Rua das Flores"
    assert data["type"] == "HOUSE"


async def test_create_address_commercial(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    owner_id = await _create_owner_via_api(client, headers)
    response = await client.post(
        f"/api/v1/owners/{owner_id}/addresses",
        json=_valid_address_payload(type="COMMERCIAL"),
        headers=headers,
    )
    assert response.status_code == 201
    assert response.json()["type"] == "COMMERCIAL"


async def test_create_address_complement_optional(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    owner_id = await _create_owner_via_api(client, headers)
    payload = _valid_address_payload()
    payload.pop("complement")
    response = await client.post(
        f"/api/v1/owners/{owner_id}/addresses", json=payload, headers=headers
    )
    assert response.status_code == 201
    assert response.json()["complement"] is None


async def test_create_address_missing_required_field(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    owner_id = await _create_owner_via_api(client, headers)
    payload = _valid_address_payload()
    payload.pop("street_name")
    response = await client.post(
        f"/api/v1/owners/{owner_id}/addresses", json=payload, headers=headers
    )
    assert response.status_code == 422


async def test_create_address_invalid_type(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    owner_id = await _create_owner_via_api(client, headers)
    response = await client.post(
        f"/api/v1/owners/{owner_id}/addresses",
        json=_valid_address_payload(type="APARTMENT"),
        headers=headers,
    )
    assert response.status_code == 422


async def test_create_address_for_owner_not_managed_returns_404(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    from app.models.owner import Owner

    await _create_user(db_session)
    headers = await _auth_headers(client)
    other = Owner(name="Someone Elses")
    db_session.add(other)
    await db_session.commit()
    response = await client.post(
        f"/api/v1/owners/{other.id}/addresses",
        json=_valid_address_payload(),
        headers=headers,
    )
    assert response.status_code == 404


# --- List ---


async def test_list_addresses_empty(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    owner_id = await _create_owner_via_api(client, headers)
    response = await client.get(f"/api/v1/owners/{owner_id}/addresses", headers=headers)
    assert response.status_code == 200
    assert response.json() == []


async def test_list_addresses_for_owner(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    owner_id = await _create_owner_via_api(client, headers)
    await _create_address_via_api(client, headers, owner_id, street_name="Rua A")
    await _create_address_via_api(client, headers, owner_id, street_name="Rua B")
    response = await client.get(f"/api/v1/owners/{owner_id}/addresses", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert {a["street_name"] for a in data} == {"Rua A", "Rua B"}


async def test_list_addresses_scoped_to_owner(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    owner_a = await _create_owner_via_api(client, headers, name="Owner A")
    owner_b = await _create_owner_via_api(client, headers, name="Owner B")
    await _create_address_via_api(client, headers, owner_a, street_name="Rua A1")
    await _create_address_via_api(client, headers, owner_b, street_name="Rua B1")
    response = await client.get(f"/api/v1/owners/{owner_a}/addresses", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["street_name"] == "Rua A1"


async def test_list_addresses_for_owner_not_managed_returns_404(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    from app.models.owner import Owner

    await _create_user(db_session)
    headers = await _auth_headers(client)
    other = Owner(name="Someone Elses")
    db_session.add(other)
    await db_session.commit()
    response = await client.get(f"/api/v1/owners/{other.id}/addresses", headers=headers)
    assert response.status_code == 404


# --- Get by id ---


async def test_get_address_by_id(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    owner_id = await _create_owner_via_api(client, headers)
    address_id = await _create_address_via_api(client, headers, owner_id)
    response = await client.get(f"/api/v1/addresses/{address_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["street_name"] == "Rua das Flores"


async def test_get_address_not_found(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    response = await client.get("/api/v1/addresses/9999", headers=headers)
    assert response.status_code == 404


async def test_get_address_not_linked_to_managed_owner_returns_404(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    # Address linked to an owner the user does NOT manage
    from app.models.owner import Owner

    other = Owner(name="Someone Elses")
    db_session.add(other)
    await db_session.commit()
    addr = Address(
        owner_id=other.id,
        street_name="Hidden",
        number="1",
        neighborhood="B",
        city="C",
        state="SP",
        zip_code="00000-000",
        type="HOUSE",
    )
    db_session.add(addr)
    await db_session.commit()
    response = await client.get(f"/api/v1/addresses/{addr.id}", headers=headers)
    assert response.status_code == 404


# --- Update ---


async def test_update_address(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    owner_id = await _create_owner_via_api(client, headers)
    address_id = await _create_address_via_api(client, headers, owner_id)
    response = await client.put(
        f"/api/v1/addresses/{address_id}",
        json=_valid_address_payload(street_name="Nova Rua", number="999", type="COMMERCIAL"),
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["street_name"] == "Nova Rua"
    assert data["number"] == "999"
    assert data["type"] == "COMMERCIAL"


async def test_update_address_not_found(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    response = await client.put(
        "/api/v1/addresses/9999",
        json=_valid_address_payload(),
        headers=headers,
    )
    assert response.status_code == 404


async def test_update_address_not_linked_to_managed_owner_returns_404(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    from app.models.owner import Owner

    other = Owner(name="Someone Elses")
    db_session.add(other)
    await db_session.commit()
    addr = Address(
        owner_id=other.id,
        street_name="Hidden",
        number="1",
        neighborhood="B",
        city="C",
        state="SP",
        zip_code="00000-000",
        type="HOUSE",
    )
    db_session.add(addr)
    await db_session.commit()
    response = await client.put(
        f"/api/v1/addresses/{addr.id}",
        json=_valid_address_payload(),
        headers=headers,
    )
    assert response.status_code == 404


# --- Delete ---


async def test_delete_address(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    owner_id = await _create_owner_via_api(client, headers)
    address_id = await _create_address_via_api(client, headers, owner_id)
    response = await client.delete(f"/api/v1/addresses/{address_id}", headers=headers)
    assert response.status_code == 204
    get = await client.get(f"/api/v1/addresses/{address_id}", headers=headers)
    assert get.status_code == 404


async def test_delete_address_not_found(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    response = await client.delete("/api/v1/addresses/9999", headers=headers)
    assert response.status_code == 404


async def test_delete_address_not_linked_to_managed_owner_returns_404(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    from app.models.owner import Owner

    other = Owner(name="Someone Elses")
    db_session.add(other)
    await db_session.commit()
    addr = Address(
        owner_id=other.id,
        street_name="Hidden",
        number="1",
        neighborhood="B",
        city="C",
        state="SP",
        zip_code="00000-000",
        type="HOUSE",
    )
    db_session.add(addr)
    await db_session.commit()
    response = await client.delete(f"/api/v1/addresses/{addr.id}", headers=headers)
    assert response.status_code == 404
