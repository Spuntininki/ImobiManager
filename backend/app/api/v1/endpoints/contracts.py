"""HTTP endpoints for the Contract resource (owner-scoped, partial updates)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import (
    get_current_active_contract,
    get_current_active_owner,
)
from app.db.session import get_db
from app.models.contract import Contract
from app.models.user import User
from app.schemas.contract import ContractCreate, ContractRead, ContractUpdate
from app.services import contract_service
from app.services.contract_service import ContractRelationError

router = APIRouter(tags=["contracts"])


# --- Nested under owners: create + list ---


@router.post(
    "/owners/{owner_id}/contracts",
    response_model=ContractRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_contract(
    owner_id: int,
    payload: ContractCreate,
    _user: User = Depends(get_current_active_owner),
    session: AsyncSession = Depends(get_db),
) -> ContractRead:
    try:
        contract = await contract_service.create_contract(session, payload, owner_id)
    except ContractRelationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(e),
        ) from None
    return ContractRead.model_validate(contract)


@router.get(
    "/owners/{owner_id}/contracts",
    response_model=list[ContractRead],
)
async def list_contracts_for_owner(
    owner_id: int,
    _user: User = Depends(get_current_active_owner),
    session: AsyncSession = Depends(get_db),
) -> list[ContractRead]:
    contracts = await contract_service.list_contracts_for_owner(session, owner_id)
    return [ContractRead.model_validate(c) for c in contracts]


# --- Flat routes: get / patch / delete (scoped via get_current_active_contract) ---


@router.get("/contracts/{contract_id}", response_model=ContractRead)
async def get_contract(
    contract: Contract = Depends(get_current_active_contract),
) -> ContractRead:
    return ContractRead.model_validate(contract)


@router.patch("/contracts/{contract_id}", response_model=ContractRead)
async def update_contract(
    contract_id: int,
    payload: ContractUpdate,
    _contract: Contract = Depends(get_current_active_contract),
    session: AsyncSession = Depends(get_db),
) -> ContractRead:
    try:
        updated = await contract_service.update_contract(
            session, contract_id, payload, _contract.owner_id
        )
    except ContractRelationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(e),
        ) from None
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
    return ContractRead.model_validate(updated)


@router.delete("/contracts/{contract_id}", status_code=status.HTTP_204_NO_CONTENT)
# TODO(phase future): replace physical delete with soft delete.
async def delete_contract(
    contract_id: int,
    _contract: Contract = Depends(get_current_active_contract),
    session: AsyncSession = Depends(get_db),
) -> None:
    deleted = await contract_service.delete_contract(session, contract_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
