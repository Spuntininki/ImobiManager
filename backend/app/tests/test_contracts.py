"""Tests for the Contract endpoints (owner-scoped, partial updates)."""

from datetime import datetime
from decimal import Decimal

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.address import Address
from app.models.contract import Contract
from app.models.owner import Owner
from app.models.owner_renter import OwnerRenter
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
    client: AsyncClient, headers: dict[str, str], owner_id: int, name: str = "Maria"
) -> int:
    resp = await client.post(
        f"/api/v1/owners/{owner_id}/renters",
        json={"name": name, "primary_contact": "999"},
        headers=headers,
    )
    return resp.json()["id"]


async def _create_address_via_api(
    client: AsyncClient, headers: dict[str, str], owner_id: int
) -> int:
    resp = await client.post(
        f"/api/v1/owners/{owner_id}/addresses",
        json={
            "street_name": "Rua X",
            "number": "1",
            "neighborhood": "B",
            "city": "C",
            "state": "SP",
            "zip_code": "00000-000",
            "type": "HOUSE",
        },
        headers=headers,
    )
    return resp.json()["id"]


def _valid_contract_payload(renter_id: int, address_id: int) -> dict:
    return {
        "renter_id": renter_id,
        "address_id": address_id,
        "start_date": "2026-01-01T00:00:00",
        "end_date": "2027-01-01T00:00:00",
        "monthly_revenue": "1500.50",
        "deposit_value": "1500.00",
        "deposit_months": 1,
        "payment_day": 5,
    }


async def _setup_owner_with_renter_and_address(
    client: AsyncClient, headers: dict[str, str]
) -> tuple[int, int, int]:
    owner_id = await _create_owner_via_api(client, headers)
    renter_id = await _create_renter_via_api(client, headers, owner_id)
    address_id = await _create_address_via_api(client, headers, owner_id)
    return owner_id, renter_id, address_id


async def _create_contract_via_api(
    client: AsyncClient,
    headers: dict[str, str],
    owner_id: int,
    renter_id: int,
    address_id: int,
) -> int:
    resp = await client.post(
        f"/api/v1/owners/{owner_id}/contracts",
        json=_valid_contract_payload(renter_id, address_id),
        headers=headers,
    )
    return resp.json()["id"]


# --- Auth required ---


async def test_create_contract_requires_auth(client: AsyncClient) -> None:
    response = await client.post("/api/v1/owners/1/contracts", json=_valid_contract_payload(1, 1))
    assert response.status_code == 401


async def test_list_contracts_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/owners/1/contracts")
    assert response.status_code == 401


async def test_get_contract_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/contracts/1")
    assert response.status_code == 401


async def test_patch_contract_requires_auth(client: AsyncClient) -> None:
    response = await client.patch("/api/v1/contracts/1", json={"status": "ACTIVE"}, headers={})
    assert response.status_code == 401


async def test_delete_contract_requires_auth(client: AsyncClient) -> None:
    response = await client.delete("/api/v1/contracts/1")
    assert response.status_code == 401


# --- Create ---


async def test_create_contract(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    owner_id, renter_id, address_id = await _setup_owner_with_renter_and_address(client, headers)
    response = await client.post(
        f"/api/v1/owners/{owner_id}/contracts",
        json=_valid_contract_payload(renter_id, address_id),
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["owner_id"] == owner_id
    assert data["renter_id"] == renter_id
    assert data["address_id"] == address_id
    assert data["status"] == "PENDING"
    assert data["generation_date"] is not None
    # Lifecycle-dated fields are none at creation
    assert data["signed_date"] is None
    assert data["cancel_date"] is None
    assert data["contract_file_path"] is None
    # Decimal round-trip
    assert data["monthly_revenue"] == "1500.50"
    assert data["deposit_value"] == "1500.00"
    assert data["payment_day"] == 5


async def test_create_contract_missing_required_field(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    owner_id, renter_id, address_id = await _setup_owner_with_renter_and_address(client, headers)
    payload = _valid_contract_payload(renter_id, address_id)
    payload.pop("monthly_revenue")
    response = await client.post(
        f"/api/v1/owners/{owner_id}/contracts", json=payload, headers=headers
    )
    assert response.status_code == 422


async def test_create_contract_invalid_payment_day_422(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    owner_id, renter_id, address_id = await _setup_owner_with_renter_and_address(client, headers)
    payload = _valid_contract_payload(renter_id, address_id)
    payload["payment_day"] = 32
    response = await client.post(
        f"/api/v1/owners/{owner_id}/contracts", json=payload, headers=headers
    )
    assert response.status_code == 422


async def test_create_contract_renter_not_linked_to_owner_422(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    o1, r1, a1 = await _setup_owner_with_renter_and_address(client, headers)
    o2, r2, a2 = await _setup_owner_with_renter_and_address(client, headers)
    # Use o2's renter with o1's owner → not linked
    payload = _valid_contract_payload(r2, a1)
    response = await client.post(f"/api/v1/owners/{o1}/contracts", json=payload, headers=headers)
    assert response.status_code == 422


async def test_create_contract_address_not_linked_to_owner_422(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    o1, r1, a1 = await _setup_owner_with_renter_and_address(client, headers)
    o2, r2, a2 = await _setup_owner_with_renter_and_address(client, headers)
    # Use o2's address with o1's owner → not linked
    payload = _valid_contract_payload(r1, a2)
    response = await client.post(f"/api/v1/owners/{o1}/contracts", json=payload, headers=headers)
    assert response.status_code == 422


async def test_create_contract_for_unmanaged_owner_404(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    other = Owner(name="Someone Elses")
    db_session.add(other)
    await db_session.commit()
    response = await client.post(
        f"/api/v1/owners/{other.id}/contracts",
        json=_valid_contract_payload(1, 1),
        headers=headers,
    )
    assert response.status_code == 404


# --- List ---


async def test_list_contracts_empty(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    owner_id, _, _ = await _setup_owner_with_renter_and_address(client, headers)
    response = await client.get(f"/api/v1/owners/{owner_id}/contracts", headers=headers)
    assert response.status_code == 200
    assert response.json() == []


async def test_list_contracts_for_owner(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    o1, r1, a1 = await _setup_owner_with_renter_and_address(client, headers)
    o2, r2, a2 = await _setup_owner_with_renter_and_address(client, headers)
    await _create_contract_via_api(client, headers, o1, r1, a1)
    await _create_contract_via_api(client, headers, o2, r2, a2)
    response = await client.get(f"/api/v1/owners/{o1}/contracts", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["owner_id"] == o1


# --- Get by id ---


async def test_get_contract_by_id(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    o, r, a = await _setup_owner_with_renter_and_address(client, headers)
    contract_id = await _create_contract_via_api(client, headers, o, r, a)
    response = await client.get(f"/api/v1/contracts/{contract_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["owner_id"] == o


async def test_get_contract_not_found(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    response = await client.get("/api/v1/contracts/9999", headers=headers)
    assert response.status_code == 404


async def test_get_contract_not_linked_to_managed_owner_404(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Contract exists but its owner is not managed by the user → 404."""
    await _create_user(db_session)
    headers = await _auth_headers(client)
    other = Owner(name="Someone Elses")
    db_session.add(other)
    await db_session.flush()
    # Real renter + address for the unmanaged owner (FK safety).
    renter = Renter(name="Hidden Renter", primary_contact="123")
    db_session.add(renter)
    await db_session.flush()
    db_session.add(OwnerRenter(owner_id=other.id, renter_id=renter.id))
    address = Address(
        owner_id=other.id,
        street_name="Hidden",
        number="1",
        neighborhood="B",
        city="C",
        state="SP",
        zip_code="00000-000",
        type="HOUSE",
    )
    db_session.add(address)
    await db_session.flush()
    contract = Contract(
        owner_id=other.id,
        renter_id=renter.id,
        address_id=address.id,
        start_date=datetime(2026, 1, 1),
        end_date=datetime(2027, 1, 1),
        monthly_revenue=Decimal("1000.00"),
        deposit_value=Decimal("0.00"),
        deposit_months=0,
        payment_day=10,
        status="PENDING",
    )
    db_session.add(contract)
    await db_session.commit()
    response = await client.get(f"/api/v1/contracts/{contract.id}", headers=headers)
    assert response.status_code == 404


# --- Patch (partial update) ---


async def test_patch_contract_status(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    o, r, a = await _setup_owner_with_renter_and_address(client, headers)
    contract_id = await _create_contract_via_api(client, headers, o, r, a)
    response = await client.patch(
        f"/api/v1/contracts/{contract_id}",
        json={"status": "ACTIVE"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ACTIVE"
    # Other fields unchanged
    assert data["signed_date"] is None


async def test_patch_contract_signed_date(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    o, r, a = await _setup_owner_with_renter_and_address(client, headers)
    contract_id = await _create_contract_via_api(client, headers, o, r, a)
    response = await client.patch(
        f"/api/v1/contracts/{contract_id}",
        json={"signed_date": "2026-02-15T10:00:00"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["signed_date"] is not None


async def test_patch_contract_rents_and_decimal(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    o, r, a = await _setup_owner_with_renter_and_address(client, headers)
    contract_id = await _create_contract_via_api(client, headers, o, r, a)
    response = await client.patch(
        f"/api/v1/contracts/{contract_id}",
        json={"monthly_revenue": "2000.00", "deposit_months": 2},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["monthly_revenue"] == "2000.00"
    assert data["deposit_months"] == 2


async def test_patch_contract_renter_not_linked_422(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    o1, r1, a1 = await _setup_owner_with_renter_and_address(client, headers)
    o2, r2, a2 = await _setup_owner_with_renter_and_address(client, headers)
    contract_id = await _create_contract_via_api(client, headers, o1, r1, a1)
    response = await client.patch(
        f"/api/v1/contracts/{contract_id}",
        json={"renter_id": r2},
        headers=headers,
    )
    assert response.status_code == 422


async def test_patch_contract_address_not_linked_422(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    o1, r1, a1 = await _setup_owner_with_renter_and_address(client, headers)
    o2, r2, a2 = await _setup_owner_with_renter_and_address(client, headers)
    contract_id = await _create_contract_via_api(client, headers, o1, r1, a1)
    response = await client.patch(
        f"/api/v1/contracts/{contract_id}",
        json={"address_id": a2},
        headers=headers,
    )
    assert response.status_code == 422


async def test_patch_contract_invalid_status_422(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    o, r, a = await _setup_owner_with_renter_and_address(client, headers)
    contract_id = await _create_contract_via_api(client, headers, o, r, a)
    response = await client.patch(
        f"/api/v1/contracts/{contract_id}",
        json={"status": "REJECTED"},
        headers=headers,
    )
    assert response.status_code == 422


async def test_patch_contract_file_path_not_accepted_422(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """File paths are backend-only — client cannot set them."""
    await _create_user(db_session)
    headers = await _auth_headers(client)
    o, r, a = await _setup_owner_with_renter_and_address(client, headers)
    contract_id = await _create_contract_via_api(client, headers, o, r, a)
    response = await client.patch(
        f"/api/v1/contracts/{contract_id}",
        json={"contract_file_path": "/tmp/contract.pdf"},
        headers=headers,
    )
    assert response.status_code == 422


async def test_patch_contract_not_found(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    response = await client.patch(
        "/api/v1/contracts/9999", json={"status": "ACTIVE"}, headers=headers
    )
    assert response.status_code == 404


# --- Delete ---


async def test_delete_contract(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    o, r, a = await _setup_owner_with_renter_and_address(client, headers)
    contract_id = await _create_contract_via_api(client, headers, o, r, a)
    response = await client.delete(f"/api/v1/contracts/{contract_id}", headers=headers)
    assert response.status_code == 204
    get = await client.get(f"/api/v1/contracts/{contract_id}", headers=headers)
    assert get.status_code == 404


async def test_delete_contract_not_found(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    response = await client.delete("/api/v1/contracts/9999", headers=headers)
    assert response.status_code == 404


async def test_delete_contract_not_linked_to_managed_owner_404(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    other = Owner(name="Someone Elses")
    db_session.add(other)
    await db_session.flush()
    renter = Renter(name="Hidden Renter", primary_contact="123")
    db_session.add(renter)
    await db_session.flush()
    db_session.add(OwnerRenter(owner_id=other.id, renter_id=renter.id))
    address = Address(
        owner_id=other.id,
        street_name="Hidden",
        number="1",
        neighborhood="B",
        city="C",
        state="SP",
        zip_code="00000-000",
        type="HOUSE",
    )
    db_session.add(address)
    await db_session.flush()
    contract = Contract(
        owner_id=other.id,
        renter_id=renter.id,
        address_id=address.id,
        start_date=datetime(2026, 1, 1),
        end_date=datetime(2027, 1, 1),
        monthly_revenue=Decimal("1000.00"),
        deposit_value=Decimal("0.00"),
        deposit_months=0,
        payment_day=10,
        status="PENDING",
    )
    db_session.add(contract)
    await db_session.commit()
    response = await client.delete(f"/api/v1/contracts/{contract.id}", headers=headers)
    assert response.status_code == 404
