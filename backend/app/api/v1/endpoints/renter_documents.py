"""HTTP endpoints for the RenterDocument resource (owner-scoped, masked reads)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_active_renter
from app.db.session import get_db
from app.models.renter import Renter
from app.schemas.renter_document import (
    RenterDocumentCreate,
    RenterDocumentRead,
    RenterDocumentUpdate,
)
from app.services import renter_document_service
from app.services.renter_document_service import IntegrityError

router = APIRouter(tags=["renter_documents"])


@router.post(
    "/renters/{renter_id}/documents",
    response_model=RenterDocumentRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_document(
    renter_id: int,
    payload: RenterDocumentCreate,
    _renter: Renter = Depends(get_current_active_renter),
    session: AsyncSession = Depends(get_db),
) -> RenterDocumentRead:
    try:
        doc = await renter_document_service.create_document(session, renter_id, payload)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Document of this type already exists for this renter",
        ) from None
    return RenterDocumentRead.model_validate(doc)


@router.get(
    "/renters/{renter_id}/documents",
    response_model=list[RenterDocumentRead],
)
async def list_documents(
    renter_id: int,
    _renter: Renter = Depends(get_current_active_renter),
    session: AsyncSession = Depends(get_db),
) -> list[RenterDocumentRead]:
    docs = await renter_document_service.list_documents_for_renter(session, renter_id)
    return [RenterDocumentRead.model_validate(d) for d in docs]


@router.get(
    "/renters/{renter_id}/documents/{document_id}",
    response_model=RenterDocumentRead,
)
async def get_document(
    document_id: int,
    _renter: Renter = Depends(get_current_active_renter),
    session: AsyncSession = Depends(get_db),
) -> RenterDocumentRead:
    doc = await renter_document_service.get_document(session, document_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    # Defense in depth: never leak a document for a different renter than
    # the scoped one. (document_id is independent of renter_id in the URL.)
    if doc.renter_id != _renter.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return RenterDocumentRead.model_validate(doc)


@router.put(
    "/renters/{renter_id}/documents/{document_id}",
    response_model=RenterDocumentRead,
)
async def update_document(
    document_id: int,
    payload: RenterDocumentUpdate,
    renter: Renter = Depends(get_current_active_renter),
    session: AsyncSession = Depends(get_db),
) -> RenterDocumentRead:
    doc = await renter_document_service.get_document(session, document_id)
    if doc is None or doc.renter_id != renter.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    try:
        updated = await renter_document_service.update_document(session, document_id, payload)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Document of this type already exists for this renter",
        ) from None
    # update_document returns None only when the doc vanished mid-flight;
    # we already checked existence above, but guard defensively.
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return RenterDocumentRead.model_validate(updated)


@router.delete(
    "/renters/{renter_id}/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_document(
    document_id: int,
    renter: Renter = Depends(get_current_active_renter),
    session: AsyncSession = Depends(get_db),
) -> None:
    doc = await renter_document_service.get_document(session, document_id)
    if doc is None or doc.renter_id != renter.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    deleted = await renter_document_service.delete_document(session, document_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
