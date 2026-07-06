"""ImobiManager CLI — operator tooling (user provisioning, etc.)."""

import asyncio

import typer

from app.db.session import async_session_factory
from app.services import user_service

cli_app = typer.Typer(no_args_is_help=True, add_completion=False)


@cli_app.callback()
def _callback() -> None:
    """ImobiManager CLI — operator tooling."""


@cli_app.command("create-user")
def create_user_cmd(
    email: str = typer.Option(..., "--email", "-e", help="User email (unique)."),
    name: str = typer.Option(..., "--name", "-n", help="User display name."),
    password: str = typer.Option(
        ...,
        prompt=True,
        hide_input=True,
        confirmation_prompt=True,
        help="Password (prompted securely; not logged to shell history).",
    ),
) -> None:
    """Create a new ImobiManager user (operator account)."""

    async def _run() -> object | None:
        async with async_session_factory() as session:
            return await user_service.create_user(session, email, name, password)

    user = asyncio.run(_run())
    if user is None:
        typer.echo(f"Error: a user with email '{email}' already exists.", err=True)
        raise typer.Exit(code=1)
    typer.echo(f"Created user '{user.email}' (id={user.id}).")


@cli_app.command("delete-user")
def delete_user_cmd(
    email: str = typer.Option(..., "--email", "-e", help="Email of the user to delete."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt."),
) -> None:
    """Delete an ImobiManager user by email."""
    if not yes:
        confirm = typer.confirm(f"Delete user '{email}'? This cannot be undone.")
        if not confirm:
            typer.echo("Aborted.")
            raise typer.Exit(code=0)

    async def _run() -> bool:
        async with async_session_factory() as session:
            return await user_service.delete_user(session, email)

    deleted = asyncio.run(_run())
    if not deleted:
        typer.echo(f"Error: no user with email '{email}' found.", err=True)
        raise typer.Exit(code=1)
    typer.echo(f"Deleted user '{email}'.")


@cli_app.command("update-password")
def update_password_cmd(
    email: str = typer.Option(..., "--email", "-e", help="Email of the user to update."),
    password: str = typer.Option(
        ...,
        prompt=True,
        hide_input=True,
        confirmation_prompt=True,
        help="New password (prompted securely; not logged to shell history).",
    ),
) -> None:
    """Update an ImobiManager user's password by email."""

    async def _run() -> bool:
        async with async_session_factory() as session:
            return await user_service.update_password(session, email, password)

    updated = asyncio.run(_run())
    if not updated:
        typer.echo(f"Error: no user with email '{email}' found.", err=True)
        raise typer.Exit(code=1)
    typer.echo(f"Updated password for '{email}'.")
