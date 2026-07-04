"""Pydantic schemas for the Address resource."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import PropertyType


class AddressCreate(BaseModel):
    """Payload for creating an address."""

    street_name: str
    number: str
    complement: str | None = None
    neighborhood: str
    city: str
    state: str
    zip_code: str
    type: PropertyType


class AddressUpdate(BaseModel):
    """Payload for updating an address (full replacement)."""

    street_name: str
    number: str
    complement: str | None = None
    neighborhood: str
    city: str
    state: str
    zip_code: str
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
