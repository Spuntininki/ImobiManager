"""Auth dependencies: current user resolution and owner access scoping."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import decode_access_token
from app.db.session import get_db
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

    Order matters: if the owner does not exist, raise 404 (does not leak
    whether the user ever had access). If the owner exists but the user is
    not linked via user_owners, raise 403.
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
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to manage this owner",
        )
    return current_user
