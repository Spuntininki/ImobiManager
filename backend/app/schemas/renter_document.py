"""Pydantic schemas for the RenterDocument resource (masked reads)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, model_validator

from app.models.enums import DocumentType


class RenterDocumentCreate(BaseModel):
    """Payload for creating a renter document (raw document number)."""

    document_type: DocumentType
    document: str


class RenterDocumentUpdate(BaseModel):
    """Payload for updating a renter document (full replacement, raw input)."""

    document_type: DocumentType
    document: str


def _mask(document_type: DocumentType, document: str) -> str:
    """Return a masked representation that never exposes the full document."""
    if document_type is DocumentType.CPF and len(document) >= 2:
        return f"***.***.***-{document[-2:]}"
    if document_type is DocumentType.CNPJ and len(document) >= 2:
        return f"**.***.***/****-{document[-2:]}"
    if document_type is DocumentType.RG and len(document) >= 1:
        return f"**.***.***-{document[-1:]}"
    return "***"


class RenterDocumentRead(BaseModel):
    """Renter document returned by the API. The document field is masked.

    The ORM model stores the raw document number; masking happens here at
    serialization time so the full value never crosses HTTP. Backend services
    that need the raw value (e.g. contract generation) read the ORM directly.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    renter_id: int
    document_type: DocumentType
    document: str
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="after")
    def _mask_document(self) -> RenterDocumentRead:
        self.document = _mask(self.document_type, self.document)
        return self
