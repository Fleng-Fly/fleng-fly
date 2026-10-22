"""Prepare local SQLite before dev starts; never reset existing data."""

import asyncio

from alembic.config import Config
from sqlalchemy import select
from sqlalchemy.engine import make_url

from alembic import command
from app.core.config import BACKEND_ROOT, get_settings
from app.db.models import Course
from app.db.seed import seed_catalog
from app.db.session import SessionLocal, engine


async def ensure_catalog() -> None:
    try:
        async with SessionLocal() as db:
            if await db.scalar(select(Course.id).limit(1)) is None:
                await seed_catalog(db)
                print("Demo catalog loaded.")
            else:
                print("Catalog already present; use npm run db:seed to update demo content.")
    finally:
        await engine.dispose()


def main() -> None:
    settings = get_settings()
    if settings.is_production or make_url(settings.database_url).get_backend_name() != "sqlite":
        print("Automatic database preparation is local SQLite only; run db:migrate explicitly.")
        return
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    command.upgrade(config, "head")
    asyncio.run(ensure_catalog())


if __name__ == "__main__":
    main()
