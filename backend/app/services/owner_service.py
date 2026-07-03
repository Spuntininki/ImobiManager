"""Business logic for the Owner resource."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.owner import Owner
from app.schemas.owner import OwnerCreate, OwnerUpdate


async def create_owner(session: AsyncSession, payload: OwnerCreate) -> Owner:
    """Create a new owner."""
    owner = Owner(name=payload.name)
    session.add(owner)
    await session.commit()
    await session.refresh(owner)
    return owner


async def get_owner(session: AsyncSession, owner_id: int) -> Owner | None:
    """Return a single owner by id, or None if not found."""
    result = await session.execute(select(Owner).where(Owner.id == owner_id))
    return result.scalar_one_or_none()


async def list_owners(session: AsyncSession) -> list[Owner]:
    """Return all owners ordered by id."""
    result = await session.execute(select(Owner).order_by(Owner.id))
    return list(result.scalars().all())


async def update_owner(session: AsyncSession, owner_id: int, payload: OwnerUpdate) -> Owner | None:
    """Update an owner by id. Returns None if not found."""
    owner = await get_owner(session, owner_id)
    if owner is None:
        return None
    owner.name = payload.name
    await session.commit()
    await session.refresh(owner)
    return owner


async def delete_owner(session: AsyncSession, owner_id: int) -> bool:
    """Delete an owner by id. Returns True if deleted, False if not found."""
    owner = await get_owner(session, owner_id)
    if owner is None:
        return False
    await session.delete(owner)
    await session.commit()
    return True
