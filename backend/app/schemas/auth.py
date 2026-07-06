"""Pydantic schemas for authentication."""

from pydantic import BaseModel


class LoginRequest(BaseModel):
    """Login payload."""

    email: str
    password: str


class TokenResponse(BaseModel):
    """Access token returned by login."""

    user_name: str
    access_token: str
    token_type: str = "bearer"
