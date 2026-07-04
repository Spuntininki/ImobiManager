"""Business logic for the Address resource (owner-scoped)."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.address import Address
from app.schemas.address import AddressCreate, AddressUpdate


async def create_address(session: AsyncSession, payload: AddressCreate, owner_id: int) -> Address:
    """Create a new address for the given owner."""
    address = Address(owner_id=owner_id, **payload.model_dump())
    session.add(address)
    await session.commit()
    await session.refresh(address)
    return address


async def get_address(session: AsyncSession, address_id: int) -> Address | None:
    """Return a single address by id, or None if not found."""
    result = await session.execute(select(Address).where(Address.id == address_id))
    return result.scalar_one_or_none()


async def list_addresses_for_owner(session: AsyncSession, owner_id: int) -> list[Address]:
    """Return addresses for the given owner, ordered by id."""
    result = await session.execute(
        select(Address).where(Address.owner_id == owner_id).order_by(Address.id)
    )
    return list(result.scalars().all())


async def update_address(
    session: AsyncSession, address_id: int, payload: AddressUpdate
) -> Address | None:
    """Update an address by id. Returns None if not found."""
    address = await get_address(session, address_id)
    if address is None:
        return None
    for field, value in payload.model_dump().items():
        setattr(address, field, value)
    await session.commit()
    await session.refresh(address)
    return address


async def delete_address(session: AsyncSession, address_id: int) -> bool:
    """Delete an address by id.

    Returns True if deleted, False if not found.
    """
    # TODO(phase future): replace physical delete with soft delete.
    address = await get_address(session, address_id)
    if address is None:
        return False
    await session.delete(address)
    await session.commit()
    return True
