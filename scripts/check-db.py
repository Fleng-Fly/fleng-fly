"""Run from backend/: .venv/bin/python ../scripts/check-db.py."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.db.session import engine  # noqa: E402
from sqlalchemy import text  # noqa: E402


async def main():
    try:
        async with asyncio.timeout(5):
            async with engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
                version = await connection.scalar(
                    text("SELECT version_num FROM alembic_version")
                )
                print(f"PostgreSQL connected; migration: {version}")
    except Exception as exc:
        # Never print the connection URL or credentials.
        print(
            f"Database check failed ({type(exc).__name__}). "
            "Check PostgreSQL and run alembic upgrade head."
        )
        return 1
    finally:
        await engine.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
