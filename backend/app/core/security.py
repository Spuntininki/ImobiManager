"""Password hashing and verification using bcrypt directly."""

import bcrypt


def hash_password(plain: str) -> str:
    """Return a bcrypt hash of the plain password."""
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if the plain password matches the bcrypt hash."""
    return bcrypt.checkpw(plain.encode(), hashed.encode())
