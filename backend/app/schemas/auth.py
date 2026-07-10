"""Pydantic schemas for authentication."""

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Login payload."""

    email: EmailStr
    password: str = Field(..., min_length=6)


class TokenResponse(BaseModel):
    """Access token returned by login."""

    access_token: str
    token_type: str = "bearer"


class UserProfile(BaseModel):
    """Authenticated user's profile (returned by /auth/me)."""

    user_name: str
    email: str
