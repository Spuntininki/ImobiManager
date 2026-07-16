"""Business logic for the RenterDocument resource (owner-scoped transitively)."""

from sqlalchemy.exc import IntegrityError

from app.models.renter_document import RenterDocument
from app.services._document_base import BaseDocumentService

_service = BaseDocumentService(RenterDocument, RenterDocument.renter_id)

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
