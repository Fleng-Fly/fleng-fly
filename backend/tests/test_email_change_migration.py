"""Email-change migration round trip preserves existing accounts and mapped schema."""

from datetime import UTC, datetime
from pathlib import Path

from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, event, inspect, text

from alembic import command
from app.db.base import Base


def test_email_change_migration_round_trip(tmp_path):
    root = Path(__file__).resolve().parents[1]
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "alembic"))
    engine = create_engine(f"sqlite:///{tmp_path / 'email.db'}")

    @event.listens_for(engine, "connect")
    def configure(connection, _):
        connection.create_function("now", 0, lambda: datetime.now(UTC).isoformat())
        connection.execute("PRAGMA foreign_keys=ON")

    try:
        with engine.connect() as connection:
            config.attributes["connection"] = connection
            command.upgrade(config, "20261116_1200")
            connection.execute(
                text(
                    "INSERT INTO users (id, email, password_hash) VALUES "
                    "('11111111111111111111111111111111', 'kept@example.com', 'kept-hash')"
                )
            )
            connection.commit()
            command.upgrade(config, "head")
            assert "email_changes" in inspect(connection).get_table_names()
            assert compare_metadata(MigrationContext.configure(connection), Base.metadata) == []
            connection.commit()
            command.downgrade(config, "20261116_1200")
            assert "email_changes" not in inspect(connection).get_table_names()
            assert connection.scalar(text("SELECT email FROM users")) == "kept@example.com"
            connection.commit()
            command.upgrade(config, "head")
            assert connection.scalar(text("SELECT password_hash FROM users")) == "kept-hash"
    finally:
        engine.dispose()
