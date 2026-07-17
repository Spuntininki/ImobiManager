"""Shared document service logic for OwnerDocument / RenterDocument.

Both document resources have the same CRUD shape: create a row scoped to an
owner/renter, list by scope, fetch/update/delete by id within that scope.
Only the ORM model and the scope FK column differ, so this base captures the
shared implementation and the per-resource modules thin down to instantiation.

The scope column is folded into every ``WHERE`` so that a document belonging to
a different owner/renter than the URL says is reported as "not found" (None /
False) rather than leaked. Callers (endpoints) translate None → 404 and
IntegrityError → 409.
"""

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.document_schemas import BaseDocumentCreate, BaseDocumentUpdate


class BaseDocumentService:
    """Owner-/renter-scoped document CRUD, parameterised by ORM model + scope column.

    Construct once per resource (e.g. ``BaseDocumentService(OwnerDocument,
    OwnerDocument.owner_id)``) and expose its methods to the endpoint layer.
    """

    def __init__(self, model, scope_column) -> None:
        self._model = model
        self._scope_column = scope_column

    async def create_document(
        self, session: AsyncSession, scope_id: int, payload: BaseDocumentCreate
    ):
        """Create a new document for the scoped owner/renter.

        Raises ``IntegrityError`` if (scope_id, document_type) already exists —
        the endpoint catches it and translates to 409.
        """
        doc = self._model(
            **{self._scope_column.name: scope_id},
            document=payload.document,
            document_type=payload.document_type,
        )
        session.add(doc)
        await session.commit()
        await session.refresh(doc)
        return doc

    async def list_documents(self, session: AsyncSession, scope_id: int) -> list:
        """Return all documents for the scope, ordered by id."""
        result = await session.execute(
            select(self._model)
            .where(self._scope_column == scope_id)
            .order_by(self._model.id)
        )
        return list(result.scalars().all())

    async def get_document(self, session: AsyncSession, scope_id: int, document_id: int):
        """Return a single document by id within the scope, or None.

        Folding the scope into the query means a document owned by another
        owner/renter is reported as not found rather than leaked.
        """
        result = await session.execute(
            select(self._model).where(
                self._model.id == document_id,
                self._scope_column == scope_id,
            )
        )
        return result.scalar_one_or_none()

    async def update_document(
        self,
        session: AsyncSession,
        scope_id: int,
        document_id: int,
        payload: BaseDocumentUpdate,
    ):
        """Update a document by id within the scope (full replacement).

        Returns None if not found. Raises ``IntegrityError`` if the new
        (scope_id, document_type) collides with another row for the same scope.
        """
        doc = await self.get_document(session, scope_id, document_id)
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

    async def delete_document(self, session: AsyncSession, scope_id: int, document_id: int) -> bool:
        """Delete a document by id within the scope.

        Returns True if deleted, False if not found (or out of scope).
        """
        result = await session.execute(
            delete(self._model)
            .where(self._model.id == document_id, self._scope_column == scope_id)
            .returning(self._model.id)
        )
        deleted_id = result.scalar_one_or_none()
        if deleted_id is None:
            return False
        await session.commit()
        return True


# Re-exported so endpoints can import IntegrityError from the per-resource
# service modules without depending on SQLAlchemy directly.
__all__ = ["BaseDocumentService", "IntegrityError"]
