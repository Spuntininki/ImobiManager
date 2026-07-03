"""Pydantic schemas for the Owner resource."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class OwnerCreate(BaseModel):
    """Payload for creating an owner."""

    name: str


class OwnerUpdate(BaseModel):
    """Payload for updating an owner."""

    name: str


class OwnerRead(BaseModel):
    """Owner representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_at: datetime
    updated_at: datetime
