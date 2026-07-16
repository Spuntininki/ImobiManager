"""Shared Pydantic building blocks for OwnerDocument / RenterDocument schemas.

Both document resources expose the same create/update payload (a document type
plus a raw document number, validated by type-specific rules) and the same read
shape (masked document number). Only the scope-id field name differs
(``owner_id`` vs ``renter_id``), so the per-resource schema files subclass the
bases defined here and add that one field.
"""

from datetime import datetime

from pydantic import BaseModel, field_validator, model_validator

from app.core.document_validation import is_valid_cnpj, is_valid_cpf
from app.core.masking import mask_document
from app.models.enums import DocumentType

# Per-type (min, max) document-length rules. RG is free-form; CPF and CNPJ are
# fixed-length with a check-digit validation below.
_DOCUMENT_VALIDATORS: dict[DocumentType, tuple[int, int | None]] = {
    DocumentType.CPF: (11, 11),
    DocumentType.CNPJ: (14, 14),
    DocumentType.RG: (4, 20),
}


def validate_document(document_type: DocumentType, document: str) -> str:
    """Validate a raw document number against its type rules.

    CPF must be digits-only with a valid check digit; CNPJ may be alphanumeric
    (per IN RFB 2212/2024) but must be ASCII with a valid check digit; RG is a
    free-form string within its length range. Returns the document unchanged
    or raises ``ValueError`` (surfaced as a 422 by FastAPI).
    """
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
    # Check-digit validation (parity with frontend).
    if document_type is DocumentType.CPF and not is_valid_cpf(document):
        raise ValueError(f"{document_type} '{document}' failed check-digit validation")
    if document_type is DocumentType.CNPJ and not is_valid_cnpj(document):
        raise ValueError(f"{document_type} '{document}' failed check-digit validation")
    return document


class BaseDocumentCreate(BaseModel):
    """Payload base for creating a document (raw document number)."""

    document_type: DocumentType
    document: str

    @field_validator("document")
    @classmethod
    def _check_document(cls, v: str, info) -> str:
        return validate_document(info.data.get("document_type", DocumentType.CPF), v)


class BaseDocumentUpdate(BaseModel):
    """Payload base for updating a document (full replacement, raw input)."""

    document_type: DocumentType
    document: str

    @field_validator("document")
    @classmethod
    def _check_document(cls, v: str, info) -> str:
        return validate_document(info.data.get("document_type", DocumentType.CPF), v)


class DocumentReadMixin(BaseModel):
    """Read-side base: masks the raw document number at serialization time.

    The ORM model stores the raw document number; masking happens here so the
    full value never crosses HTTP. Backend services that need the raw value
    (e.g. contract generation) read the ORM directly.
    """

    id: int
    document_type: DocumentType
    document: str
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="after")
    def _mask_document(self) -> DocumentReadMixin:
        self.document = mask_document(self.document_type, self.document)
        return self
