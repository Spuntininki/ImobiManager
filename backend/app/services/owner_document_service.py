"""Business logic for the OwnerDocument resource (owner-scoped)."""

from sqlalchemy.exc import IntegrityError

from app.models.owner_document import OwnerDocument
from app.services._document_base import BaseDocumentService

_service = BaseDocumentService(OwnerDocument, OwnerDocument.owner_id)

create_document = _service.create_document
list_documents = _service.list_documents
get_document = _service.get_document
update_document = _service.update_document
delete_document = _service.delete_document

__all__ = [
    "IntegrityError",
    "create_document",
    "list_documents",
    "get_document",
    "update_document",
    "delete_document",
]
