"""Tests for the Owner CRUD endpoints (open — auth arrives in Phase 3)."""

from httpx import AsyncClient


async def test_create_owner(client: AsyncClient) -> None:
    response = await client.post("/api/v1/owners", json={"name": "João Silva"})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "João Silva"
    assert data["id"] is not None
    assert data["created_at"] is not None
    assert data["updated_at"] is not None


async def test_list_owners_empty(client: AsyncClient) -> None:
    response = await client.get("/api/v1/owners")
    assert response.status_code == 200
    assert response.json() == []


async def test_list_owners_with_data(client: AsyncClient) -> None:
    await client.post("/api/v1/owners", json={"name": "Owner A"})
    await client.post("/api/v1/owners", json={"name": "Owner B"})
    response = await client.get("/api/v1/owners")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert {o["name"] for o in data} == {"Owner A", "Owner B"}


async def test_get_owner_by_id(client: AsyncClient) -> None:
    create = await client.post("/api/v1/owners", json={"name": "Single Owner"})
    owner_id = create.json()["id"]
    response = await client.get(f"/api/v1/owners/{owner_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Single Owner"


async def test_get_owner_not_found(client: AsyncClient) -> None:
    response = await client.get("/api/v1/owners/9999")
    assert response.status_code == 404


async def test_update_owner(client: AsyncClient) -> None:
    create = await client.post("/api/v1/owners", json={"name": "Old Name"})
    owner_id = create.json()["id"]
    response = await client.put(f"/api/v1/owners/{owner_id}", json={"name": "New Name"})
    assert response.status_code == 200
    assert response.json()["name"] == "New Name"


async def test_update_owner_not_found(client: AsyncClient) -> None:
    response = await client.put("/api/v1/owners/9999", json={"name": "X"})
    assert response.status_code == 404


async def test_delete_owner(client: AsyncClient) -> None:
    create = await client.post("/api/v1/owners", json={"name": "To Delete"})
    owner_id = create.json()["id"]
    response = await client.delete(f"/api/v1/owners/{owner_id}")
    assert response.status_code == 204
    get = await client.get(f"/api/v1/owners/{owner_id}")
    assert get.status_code == 404


async def test_delete_owner_not_found(client: AsyncClient) -> None:
    response = await client.delete("/api/v1/owners/9999")
    assert response.status_code == 404
