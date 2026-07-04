"""RenterDocument ORM model mirroring the `renter_documents` table in schema.dbml."""

from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.enums import DocumentType


class RenterDocument(Base):
    """RG/CPF/CNPJ record attached to a renter. Raw number stored unencrypted."""

    __tablename__ = "renter_documents"
    __table_args__ = (
        UniqueConstraint("renter_id", "document_type", name="uq_renter_documents_renter_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    renter_id: Mapped[int] = mapped_column(ForeignKey("renters.id"), nullable=False)
    document: Mapped[str] = mapped_column(String, nullable=False)
    document_type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType, name="document_types"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
