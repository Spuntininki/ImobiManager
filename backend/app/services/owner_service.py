"""Business logic for the Owner resource."""

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.owner import Owner
from app.models.user import User
from app.models.user_owner import UserOwner
from app.schemas.owner import OwnerCreate, OwnerUpdate


async def create_owner(session: AsyncSession, payload: OwnerCreate, current_user: User) -> Owner:
    """Create a new owner and link it to the current user via user_owners."""
    owner = Owner(name=payload.name)
    session.add(owner)
    await session.flush()
    session.add(UserOwner(user_id=current_user.id, owner_id=owner.id))
    await session.commit()
    await session.refresh(owner)
    return owner


async def get_owner(session: AsyncSession, owner_id: int) -> Owner | None:
    """Return a single owner by id, or None if not found."""
    result = await session.execute(select(Owner).where(Owner.id == owner_id))
    return result.scalar_one_or_none()


async def list_owners_for_user(session: AsyncSession, current_user: User) -> list[Owner]:
    """Return owners the given user is allowed to manage, ordered by id."""
    result = await session.execute(
        select(Owner)
        .join(UserOwner, UserOwner.owner_id == Owner.id)
        .where(UserOwner.user_id == current_user.id)
        .order_by(Owner.id)
    )
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
    """Delete an owner by id, including its user_owners links.

    Returns True if deleted, False if not found.
    """
    owner = await get_owner(session, owner_id)
    if owner is None:
        return False
    # Remove user_owners links first via bulk delete to avoid the FK
    # violation when the owner row is flushed.
    await session.execute(delete(UserOwner).where(UserOwner.owner_id == owner_id))
    await session.delete(owner)
    await session.commit()
    return True
