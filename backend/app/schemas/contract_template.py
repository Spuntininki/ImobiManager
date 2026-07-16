"""Pydantic schemas for the ContractTemplate resource.

Read schemas are used by future admin CRUD endpoints. The contract PDF
generation pipeline does not round-trip through these — it reads the raw
``content`` / ``style`` JSONB columns directly off the ORM model.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ContractTemplateRead(BaseModel):
    """ContractTemplate representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    description: str | None
    content: dict
    style: dict
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ContractTemplateCreate(BaseModel):
    """Payload for creating a contract template.

    ``code`` must be unique. ``is_active`` defaults to True so newly-created
    rows are immediately selectable.
    """

    model_config = ConfigDict(extra="forbid")

    code: str
    description: str | None = None
    content: dict
    style: dict
    is_active: bool = True
