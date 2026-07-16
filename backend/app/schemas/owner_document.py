"""Pydantic schemas for the OwnerDocument resource (masked reads)."""

from pydantic import ConfigDict

from app.schemas.document_schemas import (
    BaseDocumentCreate,
    BaseDocumentUpdate,
    DocumentReadMixin,
)


class OwnerDocumentCreate(BaseDocumentCreate):
    """Payload for creating an owner document (raw document number)."""


class OwnerDocumentUpdate(BaseDocumentUpdate):
    """Payload for updating an owner document (full replacement, raw input)."""


class OwnerDocumentRead(DocumentReadMixin):
    """Owner document returned by the API (document field masked)."""

    model_config = ConfigDict(from_attributes=True)

    owner_id: int
