"""HTTP endpoints for the Owner resource (authenticated + scoped)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_active_owner, get_current_user
from app.db.session import get_db
from app.models.owner import Owner
from app.models.user import User
from app.schemas.owner import OwnerCreate, OwnerRead, OwnerUpdate
from app.services import owner_service

router = APIRouter(prefix="/owners", tags=["owners"])


@router.post("", response_model=OwnerRead, status_code=status.HTTP_201_CREATED)
async def create_owner(
    payload: OwnerCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> OwnerRead:
    owner = await owner_service.create_owner(session, payload, current_user)
    return OwnerRead.model_validate(owner)


@router.get("", response_model=list[OwnerRead])
async def list_owners(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[OwnerRead]:
    owners = await owner_service.list_owners_for_user(session, current_user)
    return [OwnerRead.model_validate(o) for o in owners]


@router.get("/{owner_id}", response_model=OwnerRead)
async def get_owner(
    owner: Owner = Depends(get_current_active_owner),
) -> OwnerRead:
    return OwnerRead.model_validate(owner)


@router.put("/{owner_id}", response_model=OwnerRead)
async def update_owner(
    owner_id: int,
    payload: OwnerUpdate,
    owner: Owner = Depends(get_current_active_owner),
    session: AsyncSession = Depends(get_db),
) -> OwnerRead:
    updated = await owner_service.update_owner(session, owner_id, payload)
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Owner not found")
    return OwnerRead.model_validate(updated)


@router.delete("/{owner_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_owner(
    owner_id: int,
    owner: Owner = Depends(get_current_active_owner),
    session: AsyncSession = Depends(get_db),
) -> None:
    deleted = await owner_service.delete_owner(session, owner_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Owner not found")
