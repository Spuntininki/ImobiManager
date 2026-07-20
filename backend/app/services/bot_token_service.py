"""Business logic for bot tokens.

A bot token binds a chat platform account (chat_id) to a system subject
(USER or RENTER). Tokens are polymorphic over `subject_type + subject_id`
(no FK to keep the column simple — owned-table validation lives here).

Security notes:
- Tokens are short opaque strings (default 12 chars, base32-ish URL-safe) and
  are returned only once on creation. List/get rows redact the `token` field.
- Validation (`validate_and_bind_chat`) is the single entry point the bot pod
  uses; it checks status, expiry and chat_id binding in one transactional call
  and binds chat_id on first contact.
"""

from __future__ import annotations

import secrets
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.bot_token import BotToken
from app.models.enums import BotSubjectType, BotTokenStatus
from app.models.owner_renter import OwnerRenter
from app.models.renter import Renter
from app.models.user import User
from app.models.user_owner import UserOwner


class BotTokenError(ValueError):
    """Raised for client-facing validation errors (owner/renter not allowed)."""


class BotTokenNotFoundError(LookupError):
    """Raised when a token (or token row) is not found."""


_BASE32_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"


def _generate_token_value(length: int) -> str:
    """Return an uppercase base32-ish token of exactly `length` chars.

    The token does NOT need to be crypto-strong — it identifies a low-privilege
    chat client. We use `secrets` only for the entropy source, then map bytes
    onto a chat-friendly alphabet and trim to the requested length.
    """
    nbytes = max(8, (length * 5 + 7) // 8)
    raw = secrets.token_bytes(nbytes)
    chars = [_BASE32_ALPHABET[b & 31] for b in raw]
    out = "".join(chars)
    if len(out) < length:
        out = (out + secrets.token_hex(8))[:length].upper()
    return out[:length]


async def _assert_renter_reachable_by_user(
    session: AsyncSession, user_id: int, renter_id: int
) -> Renter:
    """Return the renter if at least one of the user's owners is linked to it.

    404-only policy (consistent with the rest of the codebase): missing renter
    or unauthorized renter both raise BotTokenNotFoundError.
    """
    renter_result = await session.execute(select(Renter).where(Renter.id == renter_id))
    renter = renter_result.scalar_one_or_none()
    if renter is None:
        raise BotTokenNotFoundError("Renter not found")
    link_result = await session.execute(
        select(OwnerRenter)
        .join(UserOwner, UserOwner.owner_id == OwnerRenter.owner_id)
        .where(UserOwner.user_id == user_id, OwnerRenter.renter_id == renter_id)
    )
    if link_result.scalar_one_or_none() is None:
        raise BotTokenNotFoundError("Renter not found")
    return renter


async def create_token(
    session: AsyncSession,
    current_user: User,
    subject_type: BotSubjectType,
    renter_id: int | None,
    expires_at: datetime | None,
) -> BotToken:
    """Create a bot token bound to a subject reachable by the current user.

    - `subject_type=USER` → subject_id is always `current_user.id`; `renter_id`
      is ignored.
    - `subject_type=RENTER` → `renter_id` is required and must be a renter
      linked to one of the user's owners; subject_id becomes that renter id.
    """
    if subject_type is BotSubjectType.USER:
        subject_id = current_user.id
    else:
        if renter_id is None:
            raise BotTokenError("renter_id is required for RENTER tokens")
        await _assert_renter_reachable_by_user(session, current_user.id, renter_id)
        subject_id = renter_id

    token = BotToken(
        token=_generate_token_value(settings.bot_token_length),
        subject_type=subject_type,
        subject_id=subject_id,
        chat_id=None,
        status=BotTokenStatus.ACTIVE,
        expires_at=expires_at,
    )
    session.add(token)
    await session.commit()
    await session.refresh(token)
    return token


async def list_tokens_for_user(session: AsyncSession, current_user: User) -> list[BotToken]:
    """Return bot tokens the caller is allowed to see, ordered by id.

    Includes the user's own USER-typed tokens and RENTER-typed tokens whose
    renter is linked to one of the user's owners. Tokens whose token field is
    not redacted here — the schema layer does that.
    """
    user_tokens = await session.execute(
        select(BotToken)
        .where(
            BotToken.subject_type == BotSubjectType.USER,
            BotToken.subject_id == current_user.id,
        )
        .order_by(BotToken.id)
    )
    tokens = list(user_tokens.scalars().all())

    renter_ids_result = await session.execute(
        select(OwnerRenter.renter_id)
        .join(UserOwner, UserOwner.owner_id == OwnerRenter.owner_id)
        .where(UserOwner.user_id == current_user.id)
    )
    renter_ids = {row[0] for row in renter_ids_result.all()}
    if renter_ids:
        renter_tokens = await session.execute(
            select(BotToken)
            .where(
                BotToken.subject_type == BotSubjectType.RENTER,
                BotToken.subject_id.in_(renter_ids),
            )
            .order_by(BotToken.id)
        )
        tokens.extend(renter_tokens.scalars().all())

    tokens.sort(key=lambda t: t.id)
    return tokens


async def get_token_for_user(session: AsyncSession, current_user: User, token_id: int) -> BotToken:
    """Return a single token the caller owns; 404 otherwise."""
    tokens = await list_tokens_for_user(session, current_user)
    for t in tokens:
        if t.id == token_id:
            return t
    raise BotTokenNotFoundError("Token not found")


async def revoke_token_for_user(
    session: AsyncSession, current_user: User, token_id: int
) -> BotToken:
    """Set status=REVOKED on a token the caller owns; 404 otherwise."""
    token = await get_token_for_user(session, current_user, token_id)
    token.status = BotTokenStatus.REVOKED
    await session.commit()
    await session.refresh(token)
    return token


async def validate_and_bind_chat(
    session: AsyncSession, token_value: str, chat_id: int
) -> tuple[BotToken, bool]:
    """Validate a token from the bot pod and bind chat_id on first contact.

    Returns `(token, linked)` where `linked=False` means this call just bound
    the chat for the first time and `True` means chat_id already matched.

    Rejects (raises BotTokenNotFoundError) when:
    - the token does not exist (constant-time-ish: no enumeration info),
    - status != ACTIVE,
    - expires_at is in the past,
    - chat_id is already bound to a different chat.
    """
    result = await session.execute(select(BotToken).where(BotToken.token == token_value))
    token = result.scalar_one_or_none()
    if token is None:
        raise BotTokenNotFoundError("Invalid token")
    if token.status is not BotTokenStatus.ACTIVE:
        raise BotTokenNotFoundError("Invalid token")
    if token.expires_at is not None and token.expires_at <= datetime.now(UTC):
        raise BotTokenNotFoundError("Invalid token")
    if token.chat_id is None:
        token.chat_id = chat_id
        await session.commit()
        await session.refresh(token)
        return token, False
    if token.chat_id != chat_id:
        raise BotTokenNotFoundError("Invalid token")
    return token, True
