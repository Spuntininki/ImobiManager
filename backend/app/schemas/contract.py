"""Pydantic schemas for the Contract resource (partial updates, masked money)."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import ContractStatus


def _check_dates_ordered(
    start: datetime | None,
    end: datetime | None,
) -> None:
    """Raise ValueError if both dates are present and start >= end."""
    if start is not None and end is not None and start >= end:
        raise ValueError("start_date must be before end_date")


class ContractCreate(BaseModel):
    """Payload for creating a contract. status and generation_date are auto-set.

    `extra="forbid"` ensures clients cannot inject fields the API doesn't
    accept (notably `contract_file_path`, which is backend-only).
    """

    model_config = ConfigDict(extra="forbid")

    renter_id: int = Field(..., gt=0)
    address_id: int = Field(..., gt=0)
    start_date: datetime
    end_date: datetime
    monthly_revenue: Decimal = Field(..., gt=0)
    deposit_value: Decimal = Field(..., ge=0)
    deposit_months: int = Field(..., ge=1, le=12)
    payment_day: int = Field(..., ge=1, le=31)

    @model_validator(mode="after")
    def _validate_dates(self) -> "ContractCreate":
        _check_dates_ordered(self.start_date, self.end_date)
        return self


class ContractUpdate(BaseModel):
    """Payload for patching a contract. All fields optional, file_path excluded.

    `status`, `signed_date`, and `cancel_date` are accepted here so clients
    can advance the contract lifecycle. The `contract_file_path` field is
    intentionally absent — only the backend (future file-upload endpoint)
    sets it. `extra="forbid"` enforces this at the schema layer.
    """

    model_config = ConfigDict(extra="forbid")

    renter_id: int | None = Field(default=None, gt=0)
    address_id: int | None = Field(default=None, gt=0)
    start_date: datetime | None = None
    end_date: datetime | None = None
    monthly_revenue: Decimal | None = Field(default=None, gt=0)
    deposit_value: Decimal | None = Field(default=None, ge=0)
    deposit_months: int | None = Field(default=None, ge=1, le=12)
    payment_day: int | None = Field(default=None, ge=1, le=31)
    status: ContractStatus | None = None
    signed_date: datetime | None = None
    cancel_date: datetime | None = None

    @model_validator(mode="after")
    def _validate_dates(self) -> "ContractUpdate":
        _check_dates_ordered(self.start_date, self.end_date)
        return self


class ContractRead(BaseModel):
    """Contract representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    renter_id: int
    address_id: int
    start_date: datetime
    end_date: datetime
    monthly_revenue: Decimal
    deposit_value: Decimal
    deposit_months: int
    payment_day: int
    generation_date: datetime
    signed_date: datetime | None
    cancel_date: datetime | None
    status: ContractStatus
    contract_file_path: str | None
    created_at: datetime
    updated_at: datetime
