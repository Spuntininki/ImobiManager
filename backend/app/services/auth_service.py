"""Business logic for authentication."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import create_access_token
from app.core.security import verify_password
from app.models.user import User


async def authenticate(
    session: AsyncSession, email: str, password: str
) -> str | None:
    """Verify credentials and return a JWT, or None if invalid."""
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(password, user.password):
        return None
    return create_access_token(user.id)
