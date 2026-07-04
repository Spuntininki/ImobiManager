"""Pydantic schemas for the OwnerDocument resource (masked reads)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, model_validator

from app.core.masking import mask_document
from app.models.enums import DocumentType


class OwnerDocumentCreate(BaseModel):
    """Payload for creating an owner document (raw document number)."""

    document_type: DocumentType
    document: str


class OwnerDocumentUpdate(BaseModel):
    """Payload for updating an owner document (full replacement, raw input)."""

    document_type: DocumentType
    document: str


class OwnerDocumentRead(BaseModel):
    """Owner document returned by the API. The document field is masked.

    The ORM model stores the raw document number; masking happens here at
    serialization time so the full value never crosses HTTP. Backend services
    that need the raw value (e.g. contract generation) read the ORM directly.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    document_type: DocumentType
    document: str
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="after")
    def _mask_document(self) -> OwnerDocumentRead:
        self.document = mask_document(self.document_type, self.document)
        return self
