"""HTTP endpoints for the Contract resource (owner-scoped, partial updates)."""

import io

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import (
    get_current_active_contract,
    get_current_active_owner,
)
from app.db.session import get_db
from app.models.contract import Contract
from app.models.user import User
from app.schemas.contract import ContractCreate, ContractRead, ContractUpdate
from app.services import contract_pdf_service, contract_service
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


@router.get(
    "/contracts/{contract_id}/pdf",
    response_class=StreamingResponse,
)
async def get_contract_pdf(
    contract: Contract = Depends(get_current_active_contract),
    session: AsyncSession = Depends(get_db),
    template_code: str = "standard",
) -> StreamingResponse:
    """Stream the rendered contract PDF back to the browser.

    Auth/permission scoping reuses ``get_current_active_contract`` — the
    caller must be linked to the contract's owner. Returns the PDF inline
    (``Content-Disposition: inline``) so the browser displays it rather
    than triggering a download dialog. Switch to ``attachment; filename=...``
    if a download UX is desired later.

    A ``?template_code=`` query param overrides the default ``standard``
    template, allowing future commercial/rural variants once seeded.
    """
    try:
        pdf_bytes = await contract_pdf_service.generate_contract_pdf(
            session, contract.id, template_code
        )
    except NoResultFound:
        # The join query in the pipeline raised — contract vanished between
        # the dependency check and here. Treat as 404 to stay consistent
        # with the rest of the resource.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found"
        ) from None
    except ValueError as e:
        # ValueError from the pipeline signals a configuration/data problem
        # (missing template row, missing required document on the contract,
        # template/formatter drift). Surface as 422 so clients see it as a
        # validation/contract-state issue rather than a generic 500.
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(e),
        ) from None
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="contract-{contract.id}.pdf"'
        },
    )


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
