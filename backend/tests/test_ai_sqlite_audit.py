"""SQLite audit: real multi-process races and migration on a populated database."""

import subprocess
import sys
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import MetaData, create_engine, event, inspect, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from alembic import command
from app.db.base import Base
from app.db.models import AIUsage
from app.modules.auth.service import register_user

BACKEND = Path(__file__).resolve().parents[1]
WORKER = Path(__file__).with_name("_ai_race_worker.py")


async def make_users(db_file: Path, count: int) -> list[str]:
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_file}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    ids = []
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        for index in range(count):
            user = await register_user(
                session, email=f"u{index}@example.com", password="test-password", display_name="U"
            )
            ids.append(str(user.id))
    await engine.dispose()
    return ids


def run_workers(db_file: Path, processes: int, attempts: int, settle: bool, users: list[str]):
    start = time.time() + 4  # interpreters boot, then all fire together
    children = [
        subprocess.Popen(
            [
                sys.executable,
                str(WORKER),
                str(db_file),
                str(start),
                str(attempts),
                "1" if settle else "0",
                # Each process walks the user list from a different offset.
                ",".join(users[i % len(users) :] + users[: i % len(users)]),
            ],
            cwd=BACKEND,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for i in range(processes)
    ]
    outputs = [child.communicate(timeout=120) for child in children]
    for child, (_out, err) in zip(children, outputs, strict=True):
        assert child.returncode == 0, err
    return sum(int(out.strip()) for out, _ in outputs)


async def usage_rows(db_file: Path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_file}")
    async with async_sessionmaker(engine)() as session:
        rows = list((await session.scalars(select(AIUsage))).all())
    await engine.dispose()
    return rows


async def test_processes_cannot_exceed_one_active_request_per_user(tmp_path):
    db = tmp_path / "race.db"
    users = await make_users(db, 1)
    # 4 OS processes x 6 attempts, none settles: exactly one hold may exist.
    assert run_workers(db, 4, 6, False, users) == 1
    assert len(await usage_rows(db)) == 1


async def test_processes_cannot_exceed_daily_quota(tmp_path):
    db = tmp_path / "race.db"
    users = await make_users(db, 1)
    # Quota 5/day; every admitted request is settled as completed, freeing the slot.
    admitted = run_workers(db, 4, 30, True, users)
    rows = await usage_rows(db)
    assert admitted == len(rows) == 5
    assert all(r.status == "completed" for r in rows)


async def test_processes_cannot_exceed_global_budget(tmp_path):
    db = tmp_path / "race.db"
    users = await make_users(db, 6)
    # $1 budget / $0.40 holds, 6 users in 4 processes, nothing settles: at most 2.
    assert run_workers(db, 4, 6, False, users) == 2
    rows = await usage_rows(db)
    assert sum(r.reserved_microusd for r in rows) <= 1_000_000


# ── Migration on an existing populated SQLite database ──────────────────────


def fill(table, **given):
    """Row for a reflected table: explicit values, filler for other required columns."""
    row = dict(given)
    for column in table.columns:
        if column.name in row or column.nullable or column.server_default is not None:
            continue
        kind = str(column.type).upper()
        if column.name == "id" or "CHAR(32)" in kind or "UUID" in kind:
            row[column.name] = uuid.uuid4().hex
        elif "INT" in kind or "BOOL" in kind:
            row[column.name] = 0
        elif "DATE" in kind:
            row[column.name] = datetime(2026, 11, 10, 8, 0, tzinfo=UTC).replace(tzinfo=None)
        elif "JSON" in kind:
            row[column.name] = "{}"
        else:
            row[column.name] = "x"
    return row


def test_migration_keeps_users_history_progress_and_usage(tmp_path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'live.db').as_posix()}")

    @event.listens_for(engine, "connect")
    def configure(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")
        connection.create_function("now", 0, lambda: datetime.now(UTC).isoformat())

    config = Config(str(BACKEND / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND / "alembic"))
    tables = ["users", "profiles", "progress", "ai_conversations", "ai_messages", "ai_usage"]
    try:
        with engine.connect() as connection:
            config.attributes["connection"] = connection
            command.upgrade(config, "20261114_1200")
            meta = MetaData()
            meta.reflect(connection, only=tables)
            user = uuid.uuid4().hex
            conversation = uuid.uuid4().hex
            for name, given in [
                ("users", {"id": user, "email": "old@example.com"}),
                ("profiles", {"user_id": user, "xp": 740}),
                ("progress", {"user_id": user}),
                ("ai_conversations", {"id": conversation, "user_id": user}),
                (
                    "ai_messages",
                    {"conversation_id": conversation, "role": "user", "content": "Привет"},
                ),
                (
                    "ai_messages",
                    {"conversation_id": conversation, "role": "assistant", "content": "Hi"},
                ),
                ("ai_usage", {"user_id": user, "created_at": datetime(2026, 11, 16, 8, 30)}),
                ("ai_usage", {"user_id": user, "created_at": datetime(2026, 11, 15, 23, 59, 59)}),
            ]:
                table = meta.tables[name]
                connection.execute(table.insert().values(**fill(table, **given)))
            connection.commit()
            legacy = "id, user_id, model, status, reserved_tokens, usage, created_at, request_id"
            before = {
                name: [
                    tuple(r)
                    for r in connection.execute(
                        text(
                            f"SELECT {legacy if name == 'ai_usage' else '*'} FROM {name} ORDER BY 1"
                        )
                    )
                ]
                for name in tables
            }
            command.upgrade(config, "head")
            for name in tables[:-1]:
                after = [
                    tuple(r) for r in connection.execute(text(f"SELECT * FROM {name} ORDER BY 1"))
                ]
                assert after == before[name], name
            columns = {c["name"] for c in inspect(connection).get_columns("ai_usage")}
            kept = connection.execute(text(f"SELECT {legacy} FROM ai_usage ORDER BY 1")).all()
            assert [tuple(r) for r in kept] == before["ai_usage"]
            days = sorted(r[0] for r in connection.execute(text("SELECT day FROM ai_usage")))
            assert days == ["2026-11-15", "2026-11-16"]
            assert {"day", "reserved_microusd", "cost_microusd", "cost_source"} <= columns
            indexes = {i["name"] for i in inspect(connection).get_indexes("ai_usage")}
            assert {"ix_ai_usage_user_id", "ai_usage_request_key", "ix_ai_usage_day"} <= indexes
            assert connection.execute(text("PRAGMA foreign_key_check")).all() == []
            assert compare_metadata(MigrationContext.configure(connection), Base.metadata) == []
            # Old rows are not billed retroactively and cannot lock the new day.
            assert connection.scalar(text("SELECT sum(reserved_microusd) FROM ai_usage")) == 0
    finally:
        engine.dispose()
