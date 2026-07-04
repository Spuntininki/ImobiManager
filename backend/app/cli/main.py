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
