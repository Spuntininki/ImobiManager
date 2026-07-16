"""HTTP endpoints for the OwnerDocument resource (owner-scoped, masked reads)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_active_owner
from app.db.session import get_db
from app.models.user import User
from app.schemas.owner_document import (
    OwnerDocumentCreate,
    OwnerDocumentRead,
    OwnerDocumentUpdate,
)
from app.services import owner_document_service
from app.services.owner_document_service import IntegrityError

router = APIRouter(tags=["owner_documents"])


@router.post(
    "/owners/{owner_id}/documents",
    response_model=OwnerDocumentRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_document(
    owner_id: int,
    payload: OwnerDocumentCreate,
    _user: User = Depends(get_current_active_owner),
    session: AsyncSession = Depends(get_db),
) -> OwnerDocumentRead:
    try:
        doc = await owner_document_service.create_document(session, owner_id, payload)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Document of this type already exists for this owner",
        ) from None
    return OwnerDocumentRead.model_validate(doc)


@router.get(
    "/owners/{owner_id}/documents",
    response_model=list[OwnerDocumentRead],
)
async def list_documents(
    owner_id: int,
    _user: User = Depends(get_current_active_owner),
    session: AsyncSession = Depends(get_db),
) -> list[OwnerDocumentRead]:
    docs = await owner_document_service.list_documents_for_owner(session, owner_id)
    return [OwnerDocumentRead.model_validate(d) for d in docs]


@router.get(
    "/owners/{owner_id}/documents/{document_id}",
    response_model=OwnerDocumentRead,
)
async def get_document(
    owner_id: int,
    document_id: int,
    _user: User = Depends(get_current_active_owner),
    session: AsyncSession = Depends(get_db),
) -> OwnerDocumentRead:
    doc = await owner_document_service.get_document(session, document_id)
    if doc is None or doc.owner_id != owner_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return OwnerDocumentRead.model_validate(doc)


@router.put(
    "/owners/{owner_id}/documents/{document_id}",
    response_model=OwnerDocumentRead,
)
async def update_document(
    owner_id: int,
    document_id: int,
    payload: OwnerDocumentUpdate,
    _user: User = Depends(get_current_active_owner),
    session: AsyncSession = Depends(get_db),
) -> OwnerDocumentRead:
    doc = await owner_document_service.get_document(session, document_id)
    if doc is None or doc.owner_id != owner_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    try:
        updated = await owner_document_service.update_document(session, document_id, payload)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Document of this type already exists for this owner",
        ) from None
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return OwnerDocumentRead.model_validate(updated)


@router.delete(
    "/owners/{owner_id}/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_document(
    owner_id: int,
    document_id: int,
    _user: User = Depends(get_current_active_owner),
    session: AsyncSession = Depends(get_db),
) -> None:
    doc = await owner_document_service.get_document(session, document_id)
    if doc is None or doc.owner_id != owner_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    deleted = await owner_document_service.delete_document(session, document_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
