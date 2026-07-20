"""Machine-to-machine endpoint for the bot pod to push audit message logs.

Auth via `X-Bot-Api-Key`. Logs are batched by the bot and POSTed
fire-and-forget; this endpoint only appends rows. Returns the count inserted
so the bot can log skipped rows.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import verify_bot_api_key
from app.db.session import get_db
from app.schemas.bot import MessageLogBatch
from app.services import bot_message_log_service

router = APIRouter(prefix="/bot/message-logs", tags=["bot-message-logs"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_bot_api_key)],
)
async def append_message_logs(
    payload: MessageLogBatch,
    session: AsyncSession = Depends(get_db),
) -> dict[str, int]:
    inserted = await bot_message_log_service.append_logs(session, payload.logs)
    return {"inserted": inserted}
