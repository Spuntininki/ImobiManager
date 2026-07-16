"""Tests for the OwnerDocument endpoints (owner-scoped, masked reads)."""

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.owner import Owner
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


async def _create_doc_via_api(
    client: AsyncClient,
    headers: dict[str, str],
    owner_id: int,
    document_type: str = "CPF",
    document: str = _VALID_CPF,
) -> int:
    resp = await client.post(
        f"/api/v1/owners/{owner_id}/documents",
        json={"document_type": document_type, "document": document},
        headers=headers,
    )
    return resp.json()["id"]


# --- Auth required ---


async def test_create_doc_requires_auth(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/owners/1/documents",
        json={"document_type": "CPF", "document": _VALID_CPF},
    )
    assert response.status_code == 401


async def test_list_docs_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/owners/1/documents")
    assert response.status_code == 401


async def test_get_doc_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/owners/1/documents/1")
    assert response.status_code == 401


async def test_update_doc_requires_auth(client: AsyncClient) -> None:
    response = await client.put(
        "/api/v1/owners/1/documents/1",
        json={"document_type": "CPF", "document": _VALID_CPF},
    )
    assert response.status_code == 401


async def test_delete_doc_requires_auth(client: AsyncClient) -> None:
    response = await client.delete("/api/v1/owners/1/documents/1")
    assert response.status_code == 401


# --- Create ---


async def test_create_cpf_doc(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    owner_id = await _create_owner_via_api(client, headers)
    response = await client.post(
        f"/api/v1/owners/{owner_id}/documents",
        json={"document_type": "CPF", "document": _VALID_CPF},
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["owner_id"] == owner_id
    assert data["document_type"] == "CPF"
    assert data["document"] == "***.***.***-25"
    assert "52998224725" not in response.text


async def test_create_cnpj_doc_masked(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    owner_id = await _create_owner_via_api(client, headers)
    response = await client.post(
        f"/api/v1/owners/{owner_id}/documents",
        json={"document_type": "CNPJ", "document": _VALID_CNPJ},
        headers=headers,
    )
    assert response.status_code == 201
    assert response.json()["document"] == "**.***.***/****-81"


async def test_create_rg_doc_masked(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    owner_id = await _create_owner_via_api(client, headers)
    response = await client.post(
        f"/api/v1/owners/{owner_id}/documents",
        json={"document_type": "RG", "document": "1234567"},
        headers=headers,
    )
    assert response.status_code == 201
    assert response.json()["document"] == "**.***.***-7"


async def test_create_doc_for_unmanaged_owner_returns_404(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    other = Owner(name="Someone Elses")
    db_session.add(other)
    await db_session.commit()
    response = await client.post(
        f"/api/v1/owners/{other.id}/documents",
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
    await _create_doc_via_api(client, headers, owner_id, "CPF", _VALID_CPF)
    response = await client.post(
        f"/api/v1/owners/{owner_id}/documents",
        json={"document_type": "CPF", "document": _VALID_CPF_2},
        headers=headers,
    )
    assert response.status_code == 409


async def test_create_same_type_different_owner_ok(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    o1 = await _create_owner_via_api(client, headers, name="A")
    o2 = await _create_owner_via_api(client, headers, name="B")
    d1 = await client.post(
        f"/api/v1/owners/{o1}/documents",
        json={"document_type": "CPF", "document": _VALID_CPF},
        headers=headers,
    )
    d2 = await client.post(
        f"/api/v1/owners/{o2}/documents",
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
    response = await client.post(
        f"/api/v1/owners/{owner_id}/documents",
        json={"document_type": "PASSPORT", "document": _VALID_CPF},
        headers=headers,
    )
    assert response.status_code == 422


# --- List ---


async def test_list_docs_empty(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    owner_id = await _create_owner_via_api(client, headers)
    response = await client.get(f"/api/v1/owners/{owner_id}/documents", headers=headers)
    assert response.status_code == 200
    assert response.json() == []


async def test_list_docs_for_owner(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    owner_id = await _create_owner_via_api(client, headers)
    await _create_doc_via_api(client, headers, owner_id, "CPF", _VALID_CPF)
    await _create_doc_via_api(client, headers, owner_id, "RG", "1234567")
    response = await client.get(f"/api/v1/owners/{owner_id}/documents", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert {d["document_type"] for d in data} == {"CPF", "RG"}
    for d in data:
        assert "***" in d["document"]


async def test_list_docs_scoped_to_owner(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    o1 = await _create_owner_via_api(client, headers, name="A")
    o2 = await _create_owner_via_api(client, headers, name="B")
    await _create_doc_via_api(client, headers, o1, "CPF", _VALID_CPF)
    await _create_doc_via_api(client, headers, o2, "CPF", _VALID_CPF_2)
    response = await client.get(f"/api/v1/owners/{o1}/documents", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


async def test_list_docs_for_unmanaged_owner_returns_404(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    other = Owner(name="Someone Elses")
    db_session.add(other)
    await db_session.commit()
    response = await client.get(f"/api/v1/owners/{other.id}/documents", headers=headers)
    assert response.status_code == 404


# --- Get by id ---


async def test_get_doc_by_id(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    owner_id = await _create_owner_via_api(client, headers)
    doc_id = await _create_doc_via_api(client, headers, owner_id, "CPF", _VALID_CPF)
    response = await client.get(f"/api/v1/owners/{owner_id}/documents/{doc_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["document"] == "***.***.***-25"


async def test_get_doc_not_found(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    owner_id = await _create_owner_via_api(client, headers)
    response = await client.get(f"/api/v1/owners/{owner_id}/documents/9999", headers=headers)
    assert response.status_code == 404


async def test_get_doc_owner_id_mismatch_returns_404(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Document belongs to a different owner than the URL says → 404."""
    await _create_user(db_session)
    headers = await _auth_headers(client)
    o1 = await _create_owner_via_api(client, headers, name="A")
    o2 = await _create_owner_via_api(client, headers, name="B")
    doc_id = await _create_doc_via_api(client, headers, o1, "CPF", _VALID_CPF)
    # Request o2's document list but ask for o1's doc id.
    response = await client.get(f"/api/v1/owners/{o2}/documents/{doc_id}", headers=headers)
    assert response.status_code == 404


async def test_get_doc_for_unmanaged_owner_returns_404(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    other = Owner(name="Someone Elses")
    db_session.add(other)
    await db_session.commit()
    response = await client.get(f"/api/v1/owners/{other.id}/documents/1", headers=headers)
    assert response.status_code == 404


# --- Update ---


async def test_update_doc_number(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    owner_id = await _create_owner_via_api(client, headers)
    doc_id = await _create_doc_via_api(client, headers, owner_id, "CPF", _VALID_CPF)
    response = await client.put(
        f"/api/v1/owners/{owner_id}/documents/{doc_id}",
        json={"document_type": "CPF", "document": _VALID_CPF_2},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["document"] == "***.***.***-09"


async def test_update_doc_type_to_unused_ok(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    owner_id = await _create_owner_via_api(client, headers)
    doc_id = await _create_doc_via_api(client, headers, owner_id, "CPF", _VALID_CPF)
    response = await client.put(
        f"/api/v1/owners/{owner_id}/documents/{doc_id}",
        json={"document_type": "RG", "document": "1234567"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["document_type"] == "RG"


async def test_update_doc_type_to_existing_returns_409(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    owner_id = await _create_owner_via_api(client, headers)
    await _create_doc_via_api(client, headers, owner_id, "CPF", _VALID_CPF)
    doc_id = await _create_doc_via_api(client, headers, owner_id, "RG", "1234567")
    response = await client.put(
        f"/api/v1/owners/{owner_id}/documents/{doc_id}",
        json={"document_type": "CPF", "document": _VALID_CPF_2},
        headers=headers,
    )
    assert response.status_code == 409


async def test_update_doc_owner_id_mismatch_returns_404(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    o1 = await _create_owner_via_api(client, headers, name="A")
    o2 = await _create_owner_via_api(client, headers, name="B")
    doc_id = await _create_doc_via_api(client, headers, o1, "CPF", _VALID_CPF)
    response = await client.put(
        f"/api/v1/owners/{o2}/documents/{doc_id}",
        json={"document_type": "CPF", "document": _VALID_CPF_2},
        headers=headers,
    )
    assert response.status_code == 404


async def test_update_doc_not_found(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    owner_id = await _create_owner_via_api(client, headers)
    response = await client.put(
        f"/api/v1/owners/{owner_id}/documents/9999",
        json={"document_type": "CPF", "document": _VALID_CPF},
        headers=headers,
    )
    assert response.status_code == 404


# --- Delete ---


async def test_delete_doc(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    owner_id = await _create_owner_via_api(client, headers)
    doc_id = await _create_doc_via_api(client, headers, owner_id, "CPF", _VALID_CPF)
    response = await client.delete(f"/api/v1/owners/{owner_id}/documents/{doc_id}", headers=headers)
    assert response.status_code == 204
    get = await client.get(f"/api/v1/owners/{owner_id}/documents/{doc_id}", headers=headers)
    assert get.status_code == 404


async def test_delete_doc_not_found(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    owner_id = await _create_owner_via_api(client, headers)
    response = await client.delete(f"/api/v1/owners/{owner_id}/documents/9999", headers=headers)
    assert response.status_code == 404


async def test_delete_doc_owner_id_mismatch_returns_404(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    o1 = await _create_owner_via_api(client, headers, name="A")
    o2 = await _create_owner_via_api(client, headers, name="B")
    doc_id = await _create_doc_via_api(client, headers, o1, "CPF", _VALID_CPF)
    response = await client.delete(f"/api/v1/owners/{o2}/documents/{doc_id}", headers=headers)
    assert response.status_code == 404
