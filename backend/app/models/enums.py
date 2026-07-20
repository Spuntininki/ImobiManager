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


class BotSubjectType(enum.StrEnum):
    """Actor type a bot token represents."""

    USER = "USER"
    RENTER = "RENTER"


class BotTokenStatus(enum.StrEnum):
    """Lifecycle status of a bot token."""

    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"


class MessageDirection(enum.StrEnum):
    """Direction of a message exchanged with the chat platform."""

    IN = "IN"
    OUT = "OUT"
