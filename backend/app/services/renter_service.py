"""Business logic for the Renter resource (owner-scoped via owner_renters)."""

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.owner_renter import OwnerRenter
from app.models.renter import Renter
from app.schemas.renter import RenterCreate, RenterUpdate


async def create_renter(session: AsyncSession, payload: RenterCreate, owner_id: int) -> Renter:
    """Create a new renter and link it to the given owner via owner_renters."""
    renter = Renter(**payload.model_dump())
    session.add(renter)
    await session.flush()
    session.add(OwnerRenter(owner_id=owner_id, renter_id=renter.id))
    await session.commit()
    await session.refresh(renter)
    return renter


async def get_renter(session: AsyncSession, renter_id: int) -> Renter | None:
    """Return a single renter by id, or None if not found."""
    result = await session.execute(select(Renter).where(Renter.id == renter_id))
    return result.scalar_one_or_none()


async def list_renters_for_owner(session: AsyncSession, owner_id: int) -> list[Renter]:
    """Return renters linked to the given owner, ordered by id."""
    result = await session.execute(
        select(Renter)
        .join(OwnerRenter, OwnerRenter.renter_id == Renter.id)
        .where(OwnerRenter.owner_id == owner_id)
        .order_by(Renter.id)
    )
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
    """Delete a renter by id, including its owner_renters links.

    Returns True if deleted, False if not found.
    """
    renter = await get_renter(session, renter_id)
    if renter is None:
        return False
    # Remove owner_renters links first via bulk delete to avoid the FK
    # violation when the renter row is flushed.
    await session.execute(delete(OwnerRenter).where(OwnerRenter.renter_id == renter_id))
    await session.delete(renter)
    await session.commit()
    return True
