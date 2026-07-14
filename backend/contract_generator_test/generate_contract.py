import asyncio
import json
import sys
from pathlib import Path

# Ensure the backend package is importable
_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from app.db.session import async_session_factory  # noqa: E402
from app.core.config import settings  # noqa: E402


async def main() -> None:
    """Load doc_content.json and demonstrate a database query."""
    doc_path = Path(__file__).resolve().parent / "doc_content.json"
    with doc_path.open("r", encoding="utf-8") as arquivo:
        data = json.load(arquivo)

    # print(data["replace"])

    for content_desc, content_lines in data["content"].items():
        print(content_desc)
        print(type(content_lines["lines"]))

    async with async_session_factory() as session:
        # Example: run a raw query or use ORM models
        # from sqlalchemy import text
        # result = await session.execute(text("SELECT * FROM contracts LIMIT 5"))
        # rows = result.fetchall()
        # print(rows[1].id)
        # Placeholder – replace with actual queries as needed
        db_url = settings.database_url
        print(f"\nConnected to database: {db_url!r}")
        print("Session is ready — add your queries above.")

        # Explicit commit is not needed when using async_session_factory
        # (the session is closed automatically on exit from the `async with` block)


if __name__ == "__main__":
    asyncio.run(main())