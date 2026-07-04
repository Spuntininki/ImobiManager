"""Tests for the user service (CLI-backed user provisioning)."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.services import auth_service, user_service


async def test_create_user_success(db_session: AsyncSession) -> None:
    user = await user_service.create_user(db_session, "admin@imobi.com", "Admin", "secret123")
    assert user is not None
    assert user.email == "admin@imobi.com"
    assert user.name == "Admin"
    # The created user must be able to authenticate via the login flow.
    token = await auth_service.authenticate(db_session, "admin@imobi.com", "secret123")
    assert token is not None


async def test_create_user_duplicate_email_returns_none(db_session: AsyncSession) -> None:
    first = await user_service.create_user(db_session, "dup@imobi.com", "First", "pw1")
    assert first is not None
    second = await user_service.create_user(db_session, "dup@imobi.com", "Second", "pw2")
    assert second is None
