"""Pydantic schemas for the OwnerDocument resource (masked reads)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.core.masking import mask_document
from app.models.enums import DocumentType

_DOCUMENT_VALIDATORS: dict[DocumentType, tuple[int, int | None]] = {
    DocumentType.CPF: (11, 11),
    DocumentType.CNPJ: (14, 14),
    DocumentType.RG: (4, 20),
}


def _validate_document(document_type: DocumentType, document: str) -> str:
    """Validate document format. CPF/CNPJ must be bare digits, RG is free-form."""
    spec = _DOCUMENT_VALIDATORS.get(document_type)
    if spec is None:
        raise ValueError(f"Unknown document type: {document_type}")
    min_len, max_len = spec
    if not (min_len <= len(document) <= (max_len or 999)):
        raise ValueError(
            f"{document_type} document must be between {min_len} and "
            f"{max_len} characters, got {len(document)}"
        )
    if document_type in (DocumentType.CPF, DocumentType.CNPJ) and not document.isdigit():
        raise ValueError(f"{document_type} must contain only digits, got '{document}'")
    return document


class OwnerDocumentCreate(BaseModel):
    """Payload for creating an owner document (raw document number)."""

    document_type: DocumentType
    document: str

    @field_validator("document")
    @classmethod
    def _check_document(cls, v: str, info) -> str:
        return _validate_document(info.data.get("document_type", DocumentType.CPF), v)


class OwnerDocumentUpdate(BaseModel):
    """Payload for updating an owner document (full replacement, raw input)."""

    document_type: DocumentType
    document: str

    @field_validator("document")
    @classmethod
    def _check_document(cls, v: str, info) -> str:
        return _validate_document(info.data.get("document_type", DocumentType.CPF), v)


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
