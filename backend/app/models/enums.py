"""Enums shared across ORM models, mirroring schema.dbml."""

import enum


class DocumentType(enum.StrEnum):
    """Type of legal document (RG, CPF, CNPJ)."""

    RG = "RG"
    CPF = "CPF"
    CNPJ = "CNPJ"


class PropertyType(enum.StrEnum):
    """Property classification: HOUSE or COMMERCIAL."""

    HOUSE = "HOUSE"
    COMMERCIAL = "COMMERCIAL"


class ContractStatus(enum.StrEnum):
    """Lifecycle status of a contract."""

    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
