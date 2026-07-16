"""HTTP endpoints for the Address resource (owner-scoped, 404-only)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import (
    get_current_active_address,
    get_current_active_owner,
)
from app.db.session import get_db
from app.models.address import Address
from app.models.user import User
from app.schemas.address import AddressCreate, AddressRead, AddressUpdate
from app.services import address_service

router = APIRouter(tags=["addresses"])


# --- Nested under owners: create + list ---


@router.post(
    "/owners/{owner_id}/addresses",
    response_model=AddressRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_address(
    owner_id: int,
    payload: AddressCreate,
    _user: User = Depends(get_current_active_owner),
    session: AsyncSession = Depends(get_db),
) -> AddressRead:
    address = await address_service.create_address(session, payload, owner_id)
    return AddressRead.model_validate(address)


@router.get(
    "/owners/{owner_id}/addresses",
    response_model=list[AddressRead],
)
async def list_addresses_for_owner(
    owner_id: int,
    _user: User = Depends(get_current_active_owner),
    session: AsyncSession = Depends(get_db),
) -> list[AddressRead]:
    addresses = await address_service.list_addresses_for_owner(session, owner_id)
    return [AddressRead.model_validate(a) for a in addresses]


# --- Flat routes: get / update / delete (scoped via get_current_active_address) ---


@router.get("/addresses/{address_id}", response_model=AddressRead)
async def get_address(
    address: Address = Depends(get_current_active_address),
) -> AddressRead:
    return AddressRead.model_validate(address)


@router.put("/addresses/{address_id}", response_model=AddressRead)
async def update_address(
    address_id: int,
    payload: AddressUpdate,
    _address: Address = Depends(get_current_active_address),
    session: AsyncSession = Depends(get_db),
) -> AddressRead:
    updated = await address_service.update_address(session, address_id, payload)
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found")
    return AddressRead.model_validate(updated)


@router.delete("/addresses/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_address(
    address_id: int,
    _address: Address = Depends(get_current_active_address),
    session: AsyncSession = Depends(get_db),
) -> None:
    deleted = await address_service.delete_address(session, address_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found")
