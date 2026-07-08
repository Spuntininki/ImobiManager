"""HTTP endpoint for the owner revenue timeline dashboard feature."""

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_active_owner
from app.db.session import get_db
from app.models.user import User
from app.schemas.revenue_timeline import RevenueTimelineItem, RevenueTimelineSummary
from app.services import revenue_timeline_service

router = APIRouter(tags=["revenue-timeline"])


@router.get(
    "/owners/{owner_id}/revenue-timeline",
    response_model=list[RevenueTimelineItem],
)
async def get_owner_revenue_timeline(
    owner_id: int,
    start_date: date | None = Query(None, description="Start of the timeline window."),
    end_date: date | None = Query(None, description="End of the timeline window."),
    _user: User = Depends(get_current_active_owner),
    session: AsyncSession = Depends(get_db),
) -> list[RevenueTimelineItem]:
    """Return projected monthly revenue payments for an owner.

    Only ACTIVE contracts are included. If no date range is provided, the
    timeline defaults to the next 12 months from today.
    """
    items, _total, _count = await revenue_timeline_service.generate_owner_revenue_timeline(
        session, owner_id, start_date=start_date, end_date=end_date
    )
    return [RevenueTimelineItem.model_validate(item) for item in items]


@router.get(
    "/owners/{owner_id}/revenue-timeline/summary",
    response_model=RevenueTimelineSummary,
)
async def get_owner_revenue_timeline_summary(
    owner_id: int,
    start_date: date | None = Query(None, description="Start of the timeline window."),
    end_date: date | None = Query(None, description="End of the timeline window."),
    _user: User = Depends(get_current_active_owner),
    session: AsyncSession = Depends(get_db),
) -> RevenueTimelineSummary:
    """Return aggregated summary of projected revenue for an owner."""
    _items, total_amount, total_payments = (
        await revenue_timeline_service.generate_owner_revenue_timeline(
            session, owner_id, start_date=start_date, end_date=end_date
        )
    )
    return RevenueTimelineSummary(
        total_amount=total_amount,
        total_payments=total_payments,
    )
