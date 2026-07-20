"""Admin endpoints for managing bot tokens (authenticated via JWT).

The logged-in user issues and revokes tokens for themselves (USER) or for
renters reachable through the owners they manage (RENTER). The plain token
value is returned ONLY on creation; list/revoke responses redact it.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user
from app.db.session import get_db
from app.models.bot_token import BotToken
from app.models.user import User
from app.schemas.bot import BotTokenCreate, BotTokenRead
from app.services import bot_token_service

router = APIRouter(prefix="/bot-tokens", tags=["bot-tokens"])


def _serialize(token: BotToken, *, include_token: bool) -> BotTokenRead:
    """Serialize a BotToken; optionally expose the plain token (creation only)."""
    read = BotTokenRead.model_validate(token)
    read.token = token.token if include_token else None
    return read


@router.post("", response_model=BotTokenRead, status_code=status.HTTP_201_CREATED)
async def create_bot_token(
    payload: BotTokenCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> BotTokenRead:
    try:
        token = await bot_token_service.create_token(
            session,
            current_user=current_user,
            subject_type=payload.subject_type,
            renter_id=payload.renter_id,
            expires_at=payload.expires_at,
        )
    except bot_token_service.BotTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except bot_token_service.BotTokenNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    return _serialize(token, include_token=True)


@router.get("", response_model=list[BotTokenRead])
async def list_bot_tokens(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[BotTokenRead]:
    tokens = await bot_token_service.list_tokens_for_user(session, current_user)
    return [_serialize(t, include_token=False) for t in tokens]


@router.post("/{token_id}/revoke", response_model=BotTokenRead)
async def revoke_bot_token(
    token_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> BotTokenRead:
    try:
        token = await bot_token_service.revoke_token_for_user(session, current_user, token_id)
    except bot_token_service.BotTokenNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    return _serialize(token, include_token=False)
