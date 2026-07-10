"""Pydantic schemas for the Owner resource."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class OwnerCreate(BaseModel):
    """Payload for creating an owner."""

    name: str = Field(..., min_length=1, max_length=255)


class OwnerUpdate(BaseModel):
    """Payload for updating an owner."""

    name: str = Field(..., min_length=1, max_length=255)


class OwnerRead(BaseModel):
    """Owner representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_at: datetime
    updated_at: datetime
