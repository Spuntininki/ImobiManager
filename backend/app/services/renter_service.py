"""Business logic for the Renter resource (global to authenticated users)."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.renter import Renter
from app.schemas.renter import RenterCreate, RenterUpdate


async def create_renter(session: AsyncSession, payload: RenterCreate) -> Renter:
    """Create a new renter."""
    renter = Renter(**payload.model_dump())
    session.add(renter)
    await session.commit()
    await session.refresh(renter)
    return renter


async def get_renter(session: AsyncSession, renter_id: int) -> Renter | None:
    """Return a single renter by id, or None if not found."""
    result = await session.execute(select(Renter).where(Renter.id == renter_id))
    return result.scalar_one_or_none()


async def list_renters(session: AsyncSession) -> list[Renter]:
    """Return all renters, ordered by id."""
    result = await session.execute(select(Renter).order_by(Renter.id))
    return list(result.scalars().all())


async def update_renter(
    session: AsyncSession, renter_id: int, payload: RenterUpdate
) -> Renter | None:
    """Update a renter by id. Returns None if not found."""
    renter = await get_renter(session, renter_id)
    if renter is None:
        return None
    for field, value in payload.model_dump().items():
        setattr(renter, field, value)
    await session.commit()
    await session.refresh(renter)
    return renter


async def delete_renter(session: AsyncSession, renter_id: int) -> bool:
    """Delete a renter by id.

    Returns True if deleted, False if not found.
    """
    # TODO(phase future): replace physical delete with soft delete.
    renter = await get_renter(session, renter_id)
    if renter is None:
        return False
    await session.delete(renter)
    await session.commit()
    return True
