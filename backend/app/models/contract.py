"""Contract ORM model mirroring the `contracts` table in schema.dbml."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.enums import ContractStatus


class Contract(Base):
    """Rental agreement between an owner, a renter, and a property address."""

    __tablename__ = "contracts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("owners.id"), nullable=False)
    renter_id: Mapped[int] = mapped_column(ForeignKey("renters.id"), nullable=False)
    address_id: Mapped[int] = mapped_column(ForeignKey("addresses.id"), nullable=False)
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    monthly_revenue: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    deposit_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    deposit_months: Mapped[int] = mapped_column(Integer, nullable=False)
    payment_day: Mapped[int] = mapped_column(Integer, nullable=False)
    generation_date: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    signed_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    cancel_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[ContractStatus] = mapped_column(
        Enum(ContractStatus, name="contract_status"), nullable=False
    )
    contract_file_path: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
