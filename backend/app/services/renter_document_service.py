"""Business logic for the RenterDocument resource (owner-scoped transitively)."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.renter_document import RenterDocument
from app.schemas.renter_document import RenterDocumentCreate, RenterDocumentUpdate


async def create_document(
    session: AsyncSession, renter_id: int, payload: RenterDocumentCreate
) -> RenterDocument:
    """Create a new document for a renter.

    Raises IntegrityError if (renter_id, document_type) already exists —
    the caller (endpoint) is expected to catch and translate to 409.
    """
    doc = RenterDocument(
        renter_id=renter_id,
        document=payload.document,
        document_type=payload.document_type,
    )
    session.add(doc)
    await session.commit()
    await session.refresh(doc)
    return doc


async def list_documents_for_renter(session: AsyncSession, renter_id: int) -> list[RenterDocument]:
    """Return all documents for a renter, ordered by id."""
    result = await session.execute(
        select(RenterDocument)
        .where(RenterDocument.renter_id == renter_id)
        .order_by(RenterDocument.id)
    )
    return list(result.scalars().all())


async def get_document(session: AsyncSession, document_id: int) -> RenterDocument | None:
    """Return a single document by id, or None if not found."""
    result = await session.execute(select(RenterDocument).where(RenterDocument.id == document_id))
    return result.scalar_one_or_none()


async def update_document(
    session: AsyncSession,
    document_id: int,
    payload: RenterDocumentUpdate,
) -> RenterDocument | None:
    """Update a document by id (full replacement).

    Returns None if not found. Raises IntegrityError if the new
    (renter_id, document_type) collides with another row for the same renter.
    """
    doc = await get_document(session, document_id)
    if doc is None:
        return None
    doc.document = payload.document
    doc.document_type = payload.document_type
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise
    await session.refresh(doc)
    return doc


async def delete_document(session: AsyncSession, document_id: int) -> bool:
    """Delete a document by id.

    Returns True if deleted, False if not found.
    """
    doc = await get_document(session, document_id)
    if doc is None:
        return False
    await session.delete(doc)
    await session.commit()
    return True


# Re-export IntegrityError so endpoints can import it from the service module
# without depending on SQLAlchemy directly.
__all__ = [
    "IntegrityError",
    "create_document",
    "list_documents_for_renter",
    "get_document",
    "update_document",
    "delete_document",
]
