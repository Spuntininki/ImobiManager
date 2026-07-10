"""Tests for the RenterDocument endpoints (owner-scoped, masked reads)."""

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.renter import Renter
from app.models.user import User

_VALID_CPF = "52998224725"
_VALID_CPF_2 = "12345678909"
_VALID_CNPJ = "11222333000181"


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


async def _create_doc_via_api(
    client: AsyncClient,
    headers: dict[str, str],
    renter_id: int,
    document_type: str = "CPF",
    document: str = _VALID_CPF,
) -> int:
    resp = await client.post(
        f"/api/v1/renters/{renter_id}/documents",
        json={"document_type": document_type, "document": document},
        headers=headers,
    )
    return resp.json()["id"]


# --- Auth required ---


async def test_create_doc_requires_auth(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/renters/1/documents",
        json={"document_type": "CPF", "document": _VALID_CPF},
    )
    assert response.status_code == 401


async def test_list_docs_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/renters/1/documents")
    assert response.status_code == 401


async def test_get_doc_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/renters/1/documents/1")
    assert response.status_code == 401


async def test_update_doc_requires_auth(client: AsyncClient) -> None:
    response = await client.put(
        "/api/v1/renters/1/documents/1",
        json={"document_type": "CPF", "document": _VALID_CPF},
    )
    assert response.status_code == 401


async def test_delete_doc_requires_auth(client: AsyncClient) -> None:
    response = await client.delete("/api/v1/renters/1/documents/1")
    assert response.status_code == 401


# --- Create ---


async def test_create_cpf_doc(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    owner_id = await _create_owner_via_api(client, headers)
    renter_id = await _create_renter_via_api(client, headers, owner_id)
    response = await client.post(
        f"/api/v1/renters/{renter_id}/documents",
        json={"document_type": "CPF", "document": _VALID_CPF},
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["renter_id"] == renter_id
    assert data["document_type"] == "CPF"
    # Masked output — last 2 digits visible.
    assert data["document"] == "***.***.***-25"
    assert "52998224725" not in response.text


async def test_create_cnpj_doc_masked(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    owner_id = await _create_owner_via_api(client, headers)
    renter_id = await _create_renter_via_api(client, headers, owner_id)
    response = await client.post(
        f"/api/v1/renters/{renter_id}/documents",
        json={"document_type": "CNPJ", "document": _VALID_CNPJ},
        headers=headers,
    )
    assert response.status_code == 201
    assert response.json()["document"] == "**.***.***/****-81"


async def test_create_rg_doc_masked(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    owner_id = await _create_owner_via_api(client, headers)
    renter_id = await _create_renter_via_api(client, headers, owner_id)
    response = await client.post(
        f"/api/v1/renters/{renter_id}/documents",
        json={"document_type": "RG", "document": "1234567"},
        headers=headers,
    )
    assert response.status_code == 201
    assert response.json()["document"] == "**.***.***-7"


async def test_create_doc_for_unreachable_renter_returns_404(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Renter exists but not linked to any managed owner → 404."""
    await _create_user(db_session)
    headers = await _auth_headers(client)
    other = Renter(name="Hidden", primary_contact="123")
    db_session.add(other)
    await db_session.commit()
    response = await client.post(
        f"/api/v1/renters/{other.id}/documents",
        json={"document_type": "CPF", "document": _VALID_CPF},
        headers=headers,
    )
    assert response.status_code == 404


async def test_create_duplicate_type_returns_409(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    owner_id = await _create_owner_via_api(client, headers)
    renter_id = await _create_renter_via_api(client, headers, owner_id)
    await _create_doc_via_api(client, headers, renter_id, "CPF", _VALID_CPF)
    response = await client.post(
        f"/api/v1/renters/{renter_id}/documents",
        json={"document_type": "CPF", "document": _VALID_CPF_2},
        headers=headers,
    )
    assert response.status_code == 409


async def test_create_same_type_different_renter_ok(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Two renters can each have their own CPF — unique is per (renter, type)."""
    await _create_user(db_session)
    headers = await _auth_headers(client)
    owner_id = await _create_owner_via_api(client, headers)
    r1 = await _create_renter_via_api(client, headers, owner_id, name="A")
    r2 = await _create_renter_via_api(client, headers, owner_id, name="B")
    d1 = await client.post(
        f"/api/v1/renters/{r1}/documents",
        json={"document_type": "CPF", "document": _VALID_CPF},
        headers=headers,
    )
    d2 = await client.post(
        f"/api/v1/renters/{r2}/documents",
        json={"document_type": "CPF", "document": _VALID_CPF_2},
        headers=headers,
    )
    assert d1.status_code == 201
    assert d2.status_code == 201


async def test_create_invalid_document_type_returns_422(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    owner_id = await _create_owner_via_api(client, headers)
    renter_id = await _create_renter_via_api(client, headers, owner_id)
    response = await client.post(
        f"/api/v1/renters/{renter_id}/documents",
        json={"document_type": "PASSPORT", "document": _VALID_CPF},
        headers=headers,
    )
    assert response.status_code == 422


# --- List ---


async def test_list_docs_empty(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    owner_id = await _create_owner_via_api(client, headers)
    renter_id = await _create_renter_via_api(client, headers, owner_id)
    response = await client.get(f"/api/v1/renters/{renter_id}/documents", headers=headers)
    assert response.status_code == 200
    assert response.json() == []


async def test_list_docs_for_renter(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    owner_id = await _create_owner_via_api(client, headers)
    renter_id = await _create_renter_via_api(client, headers, owner_id)
    await _create_doc_via_api(client, headers, renter_id, "CPF", _VALID_CPF)
    await _create_doc_via_api(client, headers, renter_id, "RG", "1234567")
    response = await client.get(f"/api/v1/renters/{renter_id}/documents", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    types = {d["document_type"] for d in data}
    assert types == {"CPF", "RG"}
    # All masked.
    for d in data:
        assert "***" in d["document"]


async def test_list_docs_scoped_to_renter(client: AsyncClient, db_session: AsyncSession) -> None:
    """Documents of renter B don't appear under renter A's list."""
    await _create_user(db_session)
    headers = await _auth_headers(client)
    owner_id = await _create_owner_via_api(client, headers)
    r1 = await _create_renter_via_api(client, headers, owner_id, name="A")
    r2 = await _create_renter_via_api(client, headers, owner_id, name="B")
    await _create_doc_via_api(client, headers, r1, "CPF", _VALID_CPF)
    await _create_doc_via_api(client, headers, r2, "CPF", _VALID_CPF_2)
    response = await client.get(f"/api/v1/renters/{r1}/documents", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


async def test_list_docs_for_unreachable_renter_returns_404(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    other = Renter(name="Hidden", primary_contact="123")
    db_session.add(other)
    await db_session.commit()
    response = await client.get(f"/api/v1/renters/{other.id}/documents", headers=headers)
    assert response.status_code == 404


# --- Get by id ---


async def test_get_doc_by_id(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    owner_id = await _create_owner_via_api(client, headers)
    renter_id = await _create_renter_via_api(client, headers, owner_id)
    doc_id = await _create_doc_via_api(client, headers, renter_id, "CPF", _VALID_CPF)
    response = await client.get(f"/api/v1/renters/{renter_id}/documents/{doc_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["document"] == "***.***.***-25"


async def test_get_doc_not_found(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    owner_id = await _create_owner_via_api(client, headers)
    renter_id = await _create_renter_via_api(client, headers, owner_id)
    response = await client.get(f"/api/v1/renters/{renter_id}/documents/9999", headers=headers)
    assert response.status_code == 404


async def test_get_doc_for_unreachable_renter_returns_404(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    other = Renter(name="Hidden", primary_contact="123")
    db_session.add(other)
    await db_session.commit()
    response = await client.get(f"/api/v1/renters/{other.id}/documents/1", headers=headers)
    assert response.status_code == 404


# --- Update ---


async def test_update_doc_number(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    owner_id = await _create_owner_via_api(client, headers)
    renter_id = await _create_renter_via_api(client, headers, owner_id)
    doc_id = await _create_doc_via_api(client, headers, renter_id, "CPF", _VALID_CPF)
    response = await client.put(
        f"/api/v1/renters/{renter_id}/documents/{doc_id}",
        json={"document_type": "CPF", "document": _VALID_CPF_2},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["document"] == "***.***.***-09"


async def test_update_doc_type_to_unused_ok(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    owner_id = await _create_owner_via_api(client, headers)
    renter_id = await _create_renter_via_api(client, headers, owner_id)
    doc_id = await _create_doc_via_api(client, headers, renter_id, "CPF", _VALID_CPF)
    response = await client.put(
        f"/api/v1/renters/{renter_id}/documents/{doc_id}",
        json={"document_type": "RG", "document": "1234567"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["document_type"] == "RG"


async def test_update_doc_type_to_existing_returns_409(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Changing type to one already present for the same renter → 409."""
    await _create_user(db_session)
    headers = await _auth_headers(client)
    owner_id = await _create_owner_via_api(client, headers)
    renter_id = await _create_renter_via_api(client, headers, owner_id)
    await _create_doc_via_api(client, headers, renter_id, "CPF", _VALID_CPF)
    doc_id = await _create_doc_via_api(client, headers, renter_id, "RG", "1234567")
    response = await client.put(
        f"/api/v1/renters/{renter_id}/documents/{doc_id}",
        json={"document_type": "CPF", "document": _VALID_CPF_2},
        headers=headers,
    )
    assert response.status_code == 409


async def test_update_doc_not_found(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    owner_id = await _create_owner_via_api(client, headers)
    renter_id = await _create_renter_via_api(client, headers, owner_id)
    response = await client.put(
        f"/api/v1/renters/{renter_id}/documents/9999",
        json={"document_type": "CPF", "document": _VALID_CPF},
        headers=headers,
    )
    assert response.status_code == 404


# --- Delete ---


async def test_delete_doc(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    owner_id = await _create_owner_via_api(client, headers)
    renter_id = await _create_renter_via_api(client, headers, owner_id)
    doc_id = await _create_doc_via_api(client, headers, renter_id, "CPF", _VALID_CPF)
    response = await client.delete(
        f"/api/v1/renters/{renter_id}/documents/{doc_id}", headers=headers
    )
    assert response.status_code == 204
    get = await client.get(f"/api/v1/renters/{renter_id}/documents/{doc_id}", headers=headers)
    assert get.status_code == 404


async def test_delete_doc_not_found(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    owner_id = await _create_owner_via_api(client, headers)
    renter_id = await _create_renter_via_api(client, headers, owner_id)
    response = await client.delete(f"/api/v1/renters/{renter_id}/documents/9999", headers=headers)
    assert response.status_code == 404


async def test_delete_doc_for_unreachable_renter_returns_404(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    other = Renter(name="Hidden", primary_contact="123")
    db_session.add(other)
    await db_session.commit()
    response = await client.delete(f"/api/v1/renters/{other.id}/documents/1", headers=headers)
    assert response.status_code == 404
