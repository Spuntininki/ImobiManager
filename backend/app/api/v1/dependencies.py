"""Auth dependencies: current user resolution and owner access scoping."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import decode_access_token
from app.db.session import get_db
from app.models.address import Address
from app.models.renter import Renter
from app.models.user import User
from app.models.user_owner import UserOwner

# Token extraction from Authorization: Bearer <token>.
http_bearer = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
    session: AsyncSession = Depends(get_db),
) -> User:
    """Resolve the JWT bearer token to the authenticated User."""
    user_id = decode_access_token(credentials.credentials)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_active_owner(
    owner_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> User:
    """Ensure the requested owner exists and the current user may manage it.

    Security policy: 404-only. If the owner does not exist, or if it exists
    but the user is not linked via user_owners, raise 404. This avoids
    leaking whether an owner id is valid to a user who should not see it
    (no 403 reconnaissance surface).
    """
    from app.models.owner import Owner

    owner_result = await session.execute(select(Owner).where(Owner.id == owner_id))
    if owner_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Owner not found",
        )
    link_result = await session.execute(
        select(UserOwner).where(
            UserOwner.user_id == current_user.id,
            UserOwner.owner_id == owner_id,
        )
    )
    if link_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Owner not found",
        )
    return current_user


async def get_current_active_renter(
    renter_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Renter:
    """Ensure the requested renter exists and is reachable by the current user.

    Security policy: 404-only. If the renter does not exist, or if it exists
    but none of the owners the user manages is linked to it via owner_renters,
    raise 404. This avoids leaking whether a renter id is valid to a user
    who should not see it (no 403 reconnaissance surface).
    """
    from app.models.owner_renter import OwnerRenter

    renter_result = await session.execute(select(Renter).where(Renter.id == renter_id))
    renter = renter_result.scalar_one_or_none()
    if renter is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Renter not found",
        )
    # Check that at least one owner the user manages is linked to this renter.
    link_result = await session.execute(
        select(OwnerRenter)
        .join(UserOwner, UserOwner.owner_id == OwnerRenter.owner_id)
        .where(
            UserOwner.user_id == current_user.id,
            OwnerRenter.renter_id == renter_id,
        )
    )
    if link_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Renter not found",
        )
    return renter


async def get_current_active_address(
    address_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Address:
    """Ensure the requested address exists and is reachable by the current user.

    Security policy: 404-only. If the address does not exist, or if it exists
    but its owner is not managed by the current user (via user_owners), raise
    404. No 403 reconnaissance surface.
    """
    address_result = await session.execute(select(Address).where(Address.id == address_id))
    address = address_result.scalar_one_or_none()
    if address is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found",
        )
    link_result = await session.execute(
        select(UserOwner).where(
            UserOwner.user_id == current_user.id,
            UserOwner.owner_id == address.owner_id,
        )
    )
    if link_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found",
        )
    return address
