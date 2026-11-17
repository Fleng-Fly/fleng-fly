"""Real SQLite migrations, independent connections and restart persistence."""

import asyncio
from pathlib import Path

from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import event, inspect, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from alembic import command
from app.db.base import Base
from app.db.models import PlacementAttempt, Profile, User
from app.modules.auth.service import register_user
from app.modules.placement import service
from app.modules.placement.schemas import PlacementAnswer, PlacementAnswers
from tests.test_placement import private_answers

ROOT = Path(__file__).resolve().parents[1]


async def test_placement_upgrade_downgrade_preserves_existing_data(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'migration.sqlite3'}")

    @event.listens_for(engine.sync_engine, "connect")
    def configure_sqlite(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")
        connection.create_function("now", 0, lambda: "2026-11-16 12:00:00")

    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "alembic"))
    try:
        async with engine.connect() as connection:

            def migrate_old(sync):
                config.attributes["connection"] = sync
                command.upgrade(config, "20261116_1400")

            await connection.run_sync(migrate_old)
            await connection.commit()
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory() as db:
            user = await register_user(
                db, email="preserve@example.com", password="test-password", display_name="Keep"
            )
            user.profile.xp = 175
            user.profile.english_level = "B1"
            await db.commit()
            user_id = user.id
        async with engine.begin() as connection:

            def upgrade_and_check(sync):
                config.attributes["connection"] = sync
                command.upgrade(config, "head")
                command.upgrade(config, "head")
                assert compare_metadata(MigrationContext.configure(sync), Base.metadata) == []
                assert "placement_attempts" in inspect(sync).get_table_names()

            await connection.run_sync(upgrade_and_check)
        async with factory() as db:
            profile = await db.scalar(select(Profile).where(Profile.user_id == user_id))
            assert (profile.xp, profile.english_level) == (175, "B1")
            created = await service.start(db, user_id)
            assert created.total == 36
        async with engine.begin() as connection:

            def downgrade(sync):
                config.attributes["connection"] = sync
                command.downgrade(config, "20261116_1400")
                assert "placement_attempts" not in inspect(sync).get_table_names()
                command.upgrade(config, "head")
                assert compare_metadata(MigrationContext.configure(sync), Base.metadata) == []

            await connection.run_sync(downgrade)
        async with factory() as db:
            assert (await db.get(User, user_id)).email == "preserve@example.com"
            assert (await db.scalar(select(Profile).where(Profile.user_id == user_id))).xp == 175
    finally:
        await engine.dispose()


async def test_parallel_answers_completion_and_restart(tmp_path):
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{tmp_path / 'parallel.sqlite3'}", connect_args={"timeout": 15}
    )

    @event.listens_for(engine.sync_engine, "connect")
    def setup(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with factory() as db:
            user = await register_user(
                db,
                email="parallel@example.com",
                password="test-password",
                display_name="Concurrent",
            )
            user_id = user.id
            created = await service.start(db, user_id)
            attempt_id = created.id
            private = await db.get(PlacementAttempt, attempt_id)
            answers = private_answers(private.questions)

        async def save(question_id, option_id):
            async with factory() as db:
                return await service.save_answers(
                    db,
                    user_id,
                    attempt_id,
                    PlacementAnswers(
                        answers=[PlacementAnswer(question_id=question_id, option_id=option_id)]
                    ),
                )

        await asyncio.gather(*(save(key, value) for key, value in answers.items()))
        async with factory() as db:
            stored = await db.get(PlacementAttempt, attempt_id)
            assert stored.answers == answers

        async def finish():
            async with factory() as db:
                return (await service.complete(db, user_id, attempt_id)).model_dump(mode="json")

        results = await asyncio.gather(*(finish() for _ in range(4)))
        assert all(result == results[0] for result in results)
        assert results[0]["result"]["correct"] == 36
        await engine.dispose()
        async with factory() as db:
            restored = await service.detail(db, await service.owned(db, user_id, attempt_id))
            assert restored.model_dump(mode="json") == results[0]
            assert (await db.scalar(select(Profile).where(Profile.user_id == user_id))).xp == 0
            assert (await db.scalar(text("PRAGMA foreign_key_check"))) is None
    finally:
        await engine.dispose()
