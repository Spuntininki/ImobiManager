"""JWT access token creation and decoding."""

from datetime import UTC, datetime, timedelta

import jwt
from jwt import InvalidTokenError

from app.core.config import settings

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours


def create_access_token(
    subject: int | str, expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES
) -> str:
    """Create a signed JWT for the given subject (user id)."""
    expire = datetime.now(UTC) + timedelta(minutes=expires_minutes)
    payload = {"sub": str(subject), "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> int | None:
    """Decode a JWT and return the user id, or None if invalid/expired."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        return int(sub) if sub is not None else None
    except InvalidTokenError, ValueError, TypeError:
        return None
