"""Pydantic schemas for the Address resource."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import PropertyType


class AddressCreate(BaseModel):
    """Payload for creating an address."""

    street_name: str = Field(..., min_length=1, max_length=255)
    number: str = Field(..., min_length=1, max_length=20)
    complement: str | None = Field(default=None, max_length=255)
    neighborhood: str = Field(..., min_length=1, max_length=255)
    city: str = Field(..., min_length=1, max_length=255)
    state: str = Field(
        ...,
        min_length=2,
        max_length=2,
        pattern=r"^[A-Z]{2}$",
    )
    zip_code: str = Field(
        ...,
        pattern=r"^\d{5}-?\d{3}$",
    )
    type: PropertyType


class AddressUpdate(BaseModel):
    """Payload for updating an address (full replacement)."""

    street_name: str = Field(..., min_length=1, max_length=255)
    number: str = Field(..., min_length=1, max_length=20)
    complement: str | None = Field(default=None, max_length=255)
    neighborhood: str = Field(..., min_length=1, max_length=255)
    city: str = Field(..., min_length=1, max_length=255)
    state: str = Field(
        ...,
        min_length=2,
        max_length=2,
        pattern=r"^[A-Z]{2}$",
    )
    zip_code: str = Field(
        ...,
        pattern=r"^\d{5}-?\d{3}$",
    )
    type: PropertyType


class AddressRead(BaseModel):
    """Address representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    street_name: str
    number: str
    complement: str | None
    neighborhood: str
    city: str
    state: str
    zip_code: str
    type: PropertyType
    created_at: datetime
    updated_at: datetime
