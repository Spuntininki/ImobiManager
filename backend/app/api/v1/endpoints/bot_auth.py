"""Machine-to-machine endpoint used by the bot pod to validate a token.

Auth via `X-Bot-Api-Key` (the shared service secret). The bot pod calls this
on every inbound message after parsing the token from `/start <TOK>` or the
`TOK command` convention. On the first valid contact the chat_id is bound
to the token; subsequent calls require chat_id to match.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import verify_bot_api_key
from app.db.session import get_db
from app.schemas.bot import BotValidateRequest, BotValidateResponse
from app.services import bot_token_service

router = APIRouter(prefix="/bot/auth", tags=["bot-auth"])


@router.post(
    "/validate",
    response_model=BotValidateResponse,
    dependencies=[Depends(verify_bot_api_key)],
)
async def validate_bot_token(
    payload: BotValidateRequest,
    session: AsyncSession = Depends(get_db),
) -> BotValidateResponse:
    """Validate a token and (on first contact) bind chat_id to it."""
    try:
        token, linked = await bot_token_service.validate_and_bind_chat(
            session, payload.token, payload.chat_id
        )
    except bot_token_service.BotTokenNotFoundError as exc:
        # 401 (not 404) so the bot treats unknown tokens like revoked ones
        # without distinguishing cases.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
    return BotValidateResponse(
        token_id=token.id,
        subject_type=token.subject_type,
        subject_id=token.subject_id,
        status=token.status,
        expires_at=token.expires_at,
        linked=linked,
    )
