"""HTTP endpoints for the Contract resource (owner-scoped, partial updates)."""

import io
import re
import unicodedata

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import (
    get_current_active_contract,
    get_current_active_owner,
)
from app.db.session import get_db
from app.models.contract import Contract
from app.models.renter import Renter
from app.models.user import User
from app.schemas.contract import ContractCreate, ContractRead, ContractUpdate
from app.services import contract_pdf_service, contract_service
from app.services.contract_service import ContractRelationError

router = APIRouter(tags=["contracts"])


# Characters disallowed in filenames across common filesystems.
_ILLEGAL_FILENAME_CHARS = re.compile(r'[\x00-\x1f<>:"/\\|?*]')


# Portuguese name connector particles — dropped so the filename keeps the
# first two *names* (e.g. "João da Silva" → "Joao_Silva", not "Joao_da").
_NAME_CONNECTORS = frozenset({"da", "de", "do", "das", "dos", "e"})


def _sanitize_renter_name(name: str, fallback: str) -> str:
    """Reduce a renter name to a filename-safe ASCII slug.

    Take the first two name tokens (skipping connector particles like "da"),
    deburr accents to their ASCII base, replace illegal filename chars with
    ``_``, and return the result. Returns ``fallback`` if the name has no
    usable tokens (defensive only — the DB enforces non-empty names).
    """
    tokens = [t for t in name.split() if t.lower() not in _NAME_CONNECTORS][:2]
    if not tokens:
        return fallback
    base = " ".join(tokens)
    # NFKD puts combining marks on their own code points; drop them to deburr.
    deburred = unicodedata.normalize("NFKD", base)
    ascii_str = deburred.encode("ascii", "ignore").decode("ascii")
    sanitized = _ILLEGAL_FILENAME_CHARS.sub("_", ascii_str)
    return sanitized.replace(" ", "_") or fallback


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
    caller must be linked to the contract's owner. The response uses
    ``Content-Disposition: attachment; filename="Contrato-<renter>-<id>.pdf"``
    so the browser triggers a download dialog with a friendly, unique name.
    The renter portion comes from the first two name tokens, deburred to
    ASCII (e.g. "João da Silva" → "Joao_Silva"); the contract id guarantees
    uniqueness across same-name renters.

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
    # renter_id is non-nullable with an enforced FK, so None is impossible
    # here. Fetch the name in a cheap scalar query rather than widening the
    # contract_pdf_service return type.
    renter_name = await session.scalar(select(Renter.name).where(Renter.id == contract.renter_id))
    safe_name = _sanitize_renter_name(renter_name or "", fallback=f"contract-{contract.id}")
    filename = f"Contrato-{safe_name}-{contract.id}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
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
