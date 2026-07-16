"""Integration tests for the contract PDF streaming endpoint.

Covers auth, 404 for missing/unmanaged contracts, 422 for missing
documents, and the happy path that returns a valid PDF.
"""

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.user import User

_TEST_CPF = "52998224725"  # valid test CPF
_TEST_RG = "1234567890"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


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
        json={"name": name, "primary_contact": "+55 11 9999-9999"},
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


async def _create_owner_doc(
    client: AsyncClient, headers: dict[str, str], owner_id: int, doc_type: str, doc: str
) -> None:
    await client.post(
        f"/api/v1/owners/{owner_id}/documents",
        json={"document_type": doc_type, "document": doc},
        headers=headers,
    )


async def _create_renter_doc(
    client: AsyncClient, headers: dict[str, str], renter_id: int, doc_type: str, doc: str
) -> None:
    await client.post(
        f"/api/v1/renters/{renter_id}/documents",
        json={"document_type": doc_type, "document": doc},
        headers=headers,
    )


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


async def _full_setup(
    client: AsyncClient, headers: dict[str, str]
) -> tuple[int, int, int, int]:
    """Create owner + renter + address + documents + contract.

    Returns ``(owner_id, renter_id, address_id, contract_id)``.
    """
    owner_id = await _create_owner_via_api(client, headers)
    renter_id = await _create_renter_via_api(client, headers, owner_id)
    address_id = await _create_address_via_api(client, headers, owner_id)

    # Both parties need CPF + RG for the PDF pipeline.
    await _create_owner_doc(client, headers, owner_id, "CPF", _TEST_CPF)
    await _create_owner_doc(client, headers, owner_id, "RG", _TEST_RG)
    await _create_renter_doc(client, headers, renter_id, "CPF", _TEST_CPF)
    await _create_renter_doc(client, headers, renter_id, "RG", _TEST_RG)

    contract_id = await _create_contract_via_api(client, headers, owner_id, renter_id, address_id)

    return owner_id, renter_id, address_id, contract_id


# ---------------------------------------------------------------------------
# Auth required
# ---------------------------------------------------------------------------


async def test_get_contract_pdf_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/contracts/1/pdf")
    assert response.status_code == 401


async def test_get_contract_pdf_requires_auth_with_template_param(
    client: AsyncClient,
) -> None:
    response = await client.get("/api/v1/contracts/1/pdf?template_code=standard")
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# 404 — contract does not exist
# ---------------------------------------------------------------------------


async def test_get_contract_pdf_not_found(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _create_user(db_session)
    headers = await _auth_headers(client)
    response = await client.get("/api/v1/contracts/9999/pdf", headers=headers)
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# 422 — missing documents
# ---------------------------------------------------------------------------


async def test_get_contract_pdf_missing_owner_documents_422(
    client: AsyncClient, db_session: AsyncSession, seeded_standard_template: object
) -> None:
    """Omit owner documents → pipeline raises ValueError → 422."""
    await _create_user(db_session)
    headers = await _auth_headers(client)
    owner_id = await _create_owner_via_api(client, headers)
    renter_id = await _create_renter_via_api(client, headers, owner_id)
    address_id = await _create_address_via_api(client, headers, owner_id)
    # Only renter docs, no owner docs:
    await _create_renter_doc(client, headers, renter_id, "CPF", _TEST_CPF)
    await _create_renter_doc(client, headers, renter_id, "RG", _TEST_RG)
    contract_id = await _create_contract_via_api(client, headers, owner_id, renter_id, address_id)

    response = await client.get(
        f"/api/v1/contracts/{contract_id}/pdf", headers=headers
    )
    assert response.status_code == 422


async def test_get_contract_pdf_missing_renter_rg_422(
    client: AsyncClient, db_session: AsyncSession, seeded_standard_template: object
) -> None:
    """Omit renter RG → pipeline raises ValueError → 422."""
    await _create_user(db_session)
    headers = await _auth_headers(client)
    owner_id = await _create_owner_via_api(client, headers)
    renter_id = await _create_renter_via_api(client, headers, owner_id)
    address_id = await _create_address_via_api(client, headers, owner_id)
    # Both owner docs, but only CPF for renter:
    await _create_owner_doc(client, headers, owner_id, "CPF", _TEST_CPF)
    await _create_owner_doc(client, headers, owner_id, "RG", _TEST_RG)
    await _create_renter_doc(client, headers, renter_id, "CPF", _TEST_CPF)
    # No renter RG
    contract_id = await _create_contract_via_api(client, headers, owner_id, renter_id, address_id)

    response = await client.get(
        f"/api/v1/contracts/{contract_id}/pdf", headers=headers
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# 404 — contract owned by someone the user does not manage
# ---------------------------------------------------------------------------


async def test_get_contract_pdf_unmanaged_owner_404(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Contract exists but its owner is not linked to the current user → 404."""
    await _create_user(db_session)
    headers = await _auth_headers(client)

    # Create a contract under an unmanaged owner via direct DB insert.
    other_owner_id = await _create_owner_via_api(client, headers, "Other Owner")
    renter_id = await _create_renter_via_api(client, headers, other_owner_id, "Other Renter")
    address_id = await _create_address_via_api(client, headers, other_owner_id)
    contract_id = await _create_contract_via_api(
        client, headers, other_owner_id, renter_id, address_id
    )

    # Now create a second user who never links to that owner.
    user2 = User(email="other@test.com", name="Other User", password=hash_password("secret"))
    db_session.add(user2)
    await db_session.commit()
    resp2 = await client.post(
        "/api/v1/auth/login", json={"email": "other@test.com", "password": "secret"}
    )
    headers2 = {"Authorization": f"Bearer {resp2.json()['access_token']}"}

    response = await client.get(
        f"/api/v1/contracts/{contract_id}/pdf", headers=headers2
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Success — PDF with default template
# ---------------------------------------------------------------------------


async def test_get_contract_pdf_success(
    client: AsyncClient, db_session: AsyncSession, seeded_standard_template: object
) -> None:
    """Full setup → 200, content-type application/pdf, non-empty body."""
    await _create_user(db_session)
    headers = await _auth_headers(client)
    *_, contract_id = await _full_setup(client, headers)

    response = await client.get(
        f"/api/v1/contracts/{contract_id}/pdf", headers=headers
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["content-disposition"] == (
        f'attachment; filename="contract-{contract_id}.pdf"'
    )
    assert len(response.content) > 0
    # Verify it starts with the PDF magic number (%PDF).
    assert response.content[:4] == b"%PDF"


async def test_get_contract_pdf_success_explicit_template(
    client: AsyncClient, db_session: AsyncSession, seeded_standard_template: object
) -> None:
    """Same as above but with explicit ``?template_code=standard``."""
    await _create_user(db_session)
    headers = await _auth_headers(client)
    *_, contract_id = await _full_setup(client, headers)

    response = await client.get(
        f"/api/v1/contracts/{contract_id}/pdf?template_code=standard",
        headers=headers,
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert len(response.content) > 0
    assert response.content[:4] == b"%PDF"


async def test_get_contract_pdf_unknown_template_code_422(
    client: AsyncClient, db_session: AsyncSession, seeded_standard_template: object
) -> None:
    """Passing a non-existent template code raises 422."""
    await _create_user(db_session)
    headers = await _auth_headers(client)
    *_, contract_id = await _full_setup(client, headers)

    response = await client.get(
        f"/api/v1/contracts/{contract_id}/pdf?template_code=nonexistent",
        headers=headers,
    )
    assert response.status_code == 422
