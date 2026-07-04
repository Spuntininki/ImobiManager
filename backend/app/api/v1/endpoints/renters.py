"""HTTP endpoints for the Renter resource (owner-scoped via owner_renters)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import (
    get_current_active_owner,
    get_current_active_renter,
)
from app.db.session import get_db
from app.models.renter import Renter
from app.models.user import User
from app.schemas.renter import RenterCreate, RenterRead, RenterUpdate
from app.services import renter_service

router = APIRouter(tags=["renters"])


# --- Nested under owners: create + list ---


@router.post(
    "/owners/{owner_id}/renters",
    response_model=RenterRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_renter(
    owner_id: int,
    payload: RenterCreate,
    _user: User = Depends(get_current_active_owner),
    session: AsyncSession = Depends(get_db),
) -> RenterRead:
    renter = await renter_service.create_renter(session, payload, owner_id)
    return RenterRead.model_validate(renter)


@router.get(
    "/owners/{owner_id}/renters",
    response_model=list[RenterRead],
)
async def list_renters_for_owner(
    owner_id: int,
    _user: User = Depends(get_current_active_owner),
    session: AsyncSession = Depends(get_db),
) -> list[RenterRead]:
    renters = await renter_service.list_renters_for_owner(session, owner_id)
    return [RenterRead.model_validate(r) for r in renters]


# --- Flat routes: get / update / delete (scoped via get_current_active_renter) ---


@router.get("/renters/{renter_id}", response_model=RenterRead)
async def get_renter(
    renter: Renter = Depends(get_current_active_renter),
) -> RenterRead:
    return RenterRead.model_validate(renter)


@router.put("/renters/{renter_id}", response_model=RenterRead)
async def update_renter(
    renter_id: int,
    payload: RenterUpdate,
    _renter: Renter = Depends(get_current_active_renter),
    session: AsyncSession = Depends(get_db),
) -> RenterRead:
    updated = await renter_service.update_renter(session, renter_id, payload)
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Renter not found")
    return RenterRead.model_validate(updated)


@router.delete("/renters/{renter_id}", status_code=status.HTTP_204_NO_CONTENT)
# TODO(phase future): replace physical delete with soft delete.
async def delete_renter(
    renter_id: int,
    _renter: Renter = Depends(get_current_active_renter),
    session: AsyncSession = Depends(get_db),
) -> None:
    deleted = await renter_service.delete_renter(session, renter_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Renter not found")
