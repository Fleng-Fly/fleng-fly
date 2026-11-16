"""The AI budget migration backfills UTC days for existing usage and is reversible."""

from datetime import UTC, datetime
from pathlib import Path

from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, event, text

from alembic import command
from app.db.base import Base


def test_ai_budget_migration_backfills_day_and_round_trips(tmp_path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'budget.db').as_posix()}")

    @event.listens_for(engine, "connect")
    def configure(connection, _):
        connection.create_function("now", 0, lambda: datetime.now(UTC).isoformat())

    root = Path(__file__).resolve().parents[1]
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "alembic"))
    uid = "22222222222222222222222222222222"
    try:
        with engine.connect() as connection:
            config.attributes["connection"] = connection
            command.upgrade(config, "20261114_1200")
            connection.execute(
                text(
                    "INSERT INTO ai_usage (id, user_id, model, status, reserved_tokens, created_at)"
                    " VALUES ('33333333333333333333333333333333', :u, 'm/x', 'completed', 5,"
                    " '2026-11-15 23:59:59')"
                ),
                {"u": uid},
            )
            connection.commit()
            command.upgrade(config, "head")
            row = connection.execute(
                text("SELECT day, reserved_microusd, cost_microusd, cost_source FROM ai_usage")
            ).one()
            assert tuple(row) == ("2026-11-15", 0, None, None)
            assert compare_metadata(MigrationContext.configure(connection), Base.metadata) == []
            command.downgrade(config, "20261114_1200")
            assert connection.scalar(text("SELECT count(*) FROM ai_usage")) == 1
            command.upgrade(config, "head")
    finally:
        engine.dispose()
