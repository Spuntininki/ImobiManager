"""Pydantic schemas for the RenterDocument resource (masked reads)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.core.masking import mask_document
from app.models.enums import DocumentType

# Shared document validation logic (mirrors owner_document.py).
_DOCUMENT_VALIDATORS: dict[DocumentType, tuple[int, int | None]] = {
    DocumentType.CPF: (11, 11),
    DocumentType.CNPJ: (14, 14),
    DocumentType.RG: (4, 20),
}


def _validate_document(document_type: DocumentType, document: str) -> str:
    """Validate document format. CPF must be digits only; CNPJ may be alphanumeric (IN RFB 2212/2024)."""
    spec = _DOCUMENT_VALIDATORS.get(document_type)
    if spec is None:
        raise ValueError(f"Unknown document type: {document_type}")
    min_len, max_len = spec
    if not (min_len <= len(document) <= (max_len or 999)):
        raise ValueError(
            f"{document_type} document must be between {min_len} and "
            f"{max_len} characters, got {len(document)}"
        )
    if document_type is DocumentType.CPF and not document.isdigit():
        raise ValueError(f"{document_type} must contain only digits, got '{document}'")
    if document_type is DocumentType.CNPJ and not document.isascii():
        raise ValueError(f"{document_type} contains invalid characters, got '{document}'")
    return document


class RenterDocumentCreate(BaseModel):
    """Payload for creating a renter document (raw document number)."""

    document_type: DocumentType
    document: str

    @field_validator("document")
    @classmethod
    def _check_document(cls, v: str, info) -> str:
        return _validate_document(info.data.get("document_type", DocumentType.CPF), v)


class RenterDocumentUpdate(BaseModel):
    """Payload for updating a renter document (full replacement, raw input)."""

    document_type: DocumentType
    document: str

    @field_validator("document")
    @classmethod
    def _check_document(cls, v: str, info) -> str:
        return _validate_document(info.data.get("document_type", DocumentType.CPF), v)


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
        self.document = mask_document(self.document_type, self.document)
        return self
