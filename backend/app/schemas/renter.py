"""Pydantic schemas for the Renter resource."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RenterCreate(BaseModel):
    """Payload for creating a renter."""

    name: str
    primary_contact: str
    secondary_contact: str | None = None
    email: str | None = None


class RenterUpdate(BaseModel):
    """Payload for updating a renter (full replacement)."""

    name: str
    primary_contact: str
    secondary_contact: str | None = None
    email: str | None = None


class RenterRead(BaseModel):
    """Renter representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    primary_contact: str
    secondary_contact: str | None
    email: str | None
    created_at: datetime
    updated_at: datetime
