"""Pydantic schemas for the chat bot integration (tokens, auth, logs)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import BotSubjectType, BotTokenStatus, MessageDirection

# --- Bot token management (admin, authenticated via JWT) --------------------


class BotTokenCreate(BaseModel):
    """Payload for issuing a bot token.

    `subject_id` is polymorphic: when `subject_type=USER` it must equal the
    caller's user id (auto-set by the endpoint); when `subject_type=RENTER`
    it must be a renter id linked to one of the owners the caller manages
    (validated by the service).
    """

    model_config = ConfigDict(extra="forbid")

    subject_type: BotSubjectType
    renter_id: int | None = Field(
        default=None,
        description="Required when subject_type=RENTER. Ignored for USER.",
    )
    expires_at: datetime | None = Field(
        default=None,
        description="Optional manual expiry. Null means no expiry.",
    )


class BotTokenRead(BaseModel):
    """Bot token representation returned by the admin API.

    The `token` value is returned only once at creation time; list/get
    responses redact it to avoid shoulder-surfing.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    subject_type: BotSubjectType
    subject_id: int
    chat_id: int | None
    status: BotTokenStatus
    expires_at: datetime | None
    created_at: datetime
    updated_at: datetime
    token: str | None = Field(
        default=None,
        description="Plain token. Returned ONLY on creation; null otherwise.",
    )


# --- Machine-to-machine: validate (bot -> backend) --------------------------


class BotValidateRequest(BaseModel):
    """Body of POST /bot/auth/validate (called by the bot pod)."""

    model_config = ConfigDict(extra="forbid")

    token: str = Field(..., min_length=1)
    chat_id: int


class BotValidateResponse(BaseModel):
    """Response of POST /bot/auth/validate when the token is usable."""

    token_id: int
    subject_type: BotSubjectType
    subject_id: int
    status: BotTokenStatus
    expires_at: datetime | None
    linked: bool = Field(
        description="True when chat_id was already bound; False when this call "
        "bound it for the first time.",
    )


# --- Machine-to-machine: message logs (bot -> backend) ----------------------


class MessageLogCreate(BaseModel):
    """Single audit entry pushed by the bot pod."""

    model_config = ConfigDict(extra="forbid")

    token_id: int | None
    chat_id: int
    direction: MessageDirection
    llm_tokens_used: int = 0


class MessageLogBatch(BaseModel):
    """Batch of audit entries pushed by the bot pod (fire-and-forget)."""

    model_config = ConfigDict(extra="forbid")

    logs: list[MessageLogCreate] = Field(..., min_length=0, max_length=500)
