"""Masking helpers for sensitive document numbers (LGPD-aligned outputs).

The ORM layer stores raw document numbers; these helpers produce masked
representations for HTTP responses so the full value never crosses HTTP.
Backend services that need the raw value (e.g. contract generation) read
the ORM model directly.
"""

from app.models.enums import DocumentType


def mask_document(document_type: DocumentType, document: str) -> str:
    """Return a masked representation that never exposes the full document.

    The format mimics the BR formatting of each document type, with the
    leading digits replaced by `*` and only the last 1–2 digits visible:
      - CPF:  ***.***.***-XX   (last 2 digits)
      - CNPJ: **.***.***/****-XX (last 2 digits)
      - RG:   **.***.***-X    (last 1 digit — RG length varies)

    For inputs too short to mask meaningfully, returns "***".
    """
    if document_type is DocumentType.CPF and len(document) >= 2:
        return f"***.***.***-{document[-2:]}"
    if document_type is DocumentType.CNPJ and len(document) >= 2:
        return f"**.***.***/****-{document[-2:]}"
    if document_type is DocumentType.RG and len(document) >= 1:
        return f"**.***.***-{document[-1:]}"
    return "***"
