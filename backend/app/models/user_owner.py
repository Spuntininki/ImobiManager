"""UserOwner ORM model mirroring the `user_owners` table in schema.dbml."""

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class UserOwner(Base):
    """Links a user to the owners they are allowed to manage."""

    __tablename__ = "user_owners"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    owner_id: Mapped[int] = mapped_column(ForeignKey("owners.id"), nullable=False)
