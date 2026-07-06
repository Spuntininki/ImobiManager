"""Pydantic schemas for the Contract resource (partial updates, masked money)."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.enums import ContractStatus


class ContractCreate(BaseModel):
    """Payload for creating a contract. status and generation_date are auto-set.

    `extra="forbid"` ensures clients cannot inject fields the API doesn't
    accept (notably `*_file_path`, which is backend-only).
    """

    model_config = ConfigDict(extra="forbid")

    renter_id: int
    address_id: int
    start_date: datetime
    end_date: datetime
    monthly_revenue: Decimal
    deposit_value: Decimal
    deposit_months: int


class ContractUpdate(BaseModel):
    """Payload for patching a contract. All fields optional, *_file_path excluded.

    `status`, `signed_date`, and `cancel_date` are accepted here so clients
    can advance the contract lifecycle. The two `*_file_path` fields are
    intentionally absent — only the backend (future file-upload endpoint)
    sets them. `extra="forbid"` enforces this at the schema layer.
    """

    model_config = ConfigDict(extra="forbid")

    renter_id: int | None = None
    address_id: int | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    monthly_revenue: Decimal | None = None
    deposit_value: Decimal | None = None
    deposit_months: int | None = None
    status: ContractStatus | None = None
    signed_date: datetime | None = None
    cancel_date: datetime | None = None


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
    generation_date: datetime
    signed_date: datetime | None
    cancel_date: datetime | None
    status: ContractStatus
    unrecognized_contract_file_path: str | None
    recognized_contract_file_path: str | None
    created_at: datetime
    updated_at: datetime
