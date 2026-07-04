"""Business logic for user provisioning (used by CLI, not HTTP endpoints)."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.user import User


async def create_user(session: AsyncSession, email: str, name: str, password: str) -> User | None:
    """Create a new user with a hashed password.

    Returns the created User, or None if a user with the given email already
    exists (the caller decides how to surface the duplicate-email case, so
    this stays free of HTTP/exception-handler coupling).
    """
    existing = await session.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none() is not None:
        return None
    user = User(email=email, name=name, password=hash_password(password))
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user
