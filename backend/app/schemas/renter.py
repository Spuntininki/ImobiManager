"""Pydantic schemas for the Renter resource."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RenterCreate(BaseModel):
    """Payload for creating a renter."""

    name: str = Field(..., min_length=1, max_length=255)
    primary_contact: str = Field(
        ...,
        min_length=8,
        max_length=20,
        pattern=r"^(\+55\s?)?\d{2}\s?\d{4,5}-?\d{4}$",
    )
    secondary_contact: str | None = Field(
        default=None,
        min_length=8,
        max_length=20,
        pattern=r"^(\+55\s?)?\d{2}\s?\d{4,5}-?\d{4}$",
    )
    email: EmailStr | None = None


class RenterUpdate(BaseModel):
    """Payload for updating a renter (full replacement)."""

    name: str = Field(..., min_length=1, max_length=255)
    primary_contact: str = Field(
        ...,
        min_length=8,
        max_length=20,
        pattern=r"^(\+55\s?)?\d{2}\s?\d{4,5}-?\d{4}$",
    )
    secondary_contact: str | None = Field(
        default=None,
        min_length=8,
        max_length=20,
        pattern=r"^(\+55\s?)?\d{2}\s?\d{4,5}-?\d{4}$",
    )
    email: EmailStr | None = None


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
