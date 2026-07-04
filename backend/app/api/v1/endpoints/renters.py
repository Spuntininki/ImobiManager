"""HTTP endpoints for the Renter resource (authenticated, global scoping)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.renter import RenterCreate, RenterRead, RenterUpdate
from app.services import renter_service

router = APIRouter(prefix="/renters", tags=["renters"])


@router.post("", response_model=RenterRead, status_code=status.HTTP_201_CREATED)
async def create_renter(
    payload: RenterCreate,
    _user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> RenterRead:
    renter = await renter_service.create_renter(session, payload)
    return RenterRead.model_validate(renter)


@router.get("", response_model=list[RenterRead])
async def list_renters(
    _user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[RenterRead]:
    renters = await renter_service.list_renters(session)
    return [RenterRead.model_validate(r) for r in renters]


@router.get("/{renter_id}", response_model=RenterRead)
async def get_renter(
    renter_id: int,
    _user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> RenterRead:
    renter = await renter_service.get_renter(session, renter_id)
    if renter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Renter not found")
    return RenterRead.model_validate(renter)


@router.put("/{renter_id}", response_model=RenterRead)
async def update_renter(
    renter_id: int,
    payload: RenterUpdate,
    _user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> RenterRead:
    renter = await renter_service.update_renter(session, renter_id, payload)
    if renter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Renter not found")
    return RenterRead.model_validate(renter)


@router.delete("/{renter_id}", status_code=status.HTTP_204_NO_CONTENT)
# TODO(phase future): replace physical delete with soft delete.
async def delete_renter(
    renter_id: int,
    _user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> None:
    deleted = await renter_service.delete_renter(session, renter_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Renter not found")
