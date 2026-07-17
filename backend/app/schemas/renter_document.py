"""Pydantic schemas for the RenterDocument resource (masked reads)."""

from pydantic import ConfigDict

from app.schemas.document_schemas import (
    BaseDocumentCreate,
    BaseDocumentUpdate,
    DocumentReadMixin,
)


class RenterDocumentCreate(BaseDocumentCreate):
    """Payload for creating a renter document (raw document number)."""


class RenterDocumentUpdate(BaseDocumentUpdate):
    """Payload for updating a renter document (full replacement, raw input)."""


class RenterDocumentRead(DocumentReadMixin):
    """Renter document returned by the API (document field masked)."""

    model_config = ConfigDict(from_attributes=True)

    renter_id: int
