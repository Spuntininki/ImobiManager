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


async def test_delete_user_success(db_session: AsyncSession) -> None:
    created = await user_service.create_user(db_session, "del@imobi.com", "Del", "pw1")
    assert created is not None
    deleted = await user_service.delete_user(db_session, "del@imobi.com")
    assert deleted is True
    # The deleted user can no longer authenticate.
    token = await auth_service.authenticate(db_session, "del@imobi.com", "pw1")
    assert token is None


async def test_delete_user_not_found_returns_false(db_session: AsyncSession) -> None:
    deleted = await user_service.delete_user(db_session, "ghost@imobi.com")
    assert deleted is False


async def test_update_password_success(db_session: AsyncSession) -> None:
    await user_service.create_user(db_session, "upd@imobi.com", "Upd", "oldpw")
    updated = await user_service.update_password(db_session, "upd@imobi.com", "newpw")
    assert updated is True
    # New password authenticates; old password no longer does.
    assert await auth_service.authenticate(db_session, "upd@imobi.com", "newpw") is not None
    assert await auth_service.authenticate(db_session, "upd@imobi.com", "oldpw") is None


async def test_update_password_user_not_found_returns_false(db_session: AsyncSession) -> None:
    updated = await user_service.update_password(db_session, "ghost@imobi.com", "pw")
    assert updated is False
