"""OwnerRenter ORM model mirroring the `owner_renters` table in schema.dbml."""

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class OwnerRenter(Base):
    """Links an owner to the renters they have a rental relationship with."""

    __tablename__ = "owner_renters"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("owners.id"), nullable=False)
    renter_id: Mapped[int] = mapped_column(ForeignKey("renters.id"), nullable=False)
