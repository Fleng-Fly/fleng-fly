"""Both repository and distributed desktop schemas upgrade without losing data."""

from datetime import UTC, datetime
from pathlib import Path

import pytest
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, event, text

from alembic import command
from app.db.base import Base


@pytest.mark.parametrize("legacy_desktop", [False, True])
def test_letter_tiles_upgrade_preserves_existing_content(tmp_path, legacy_desktop):
    engine = create_engine(f"sqlite:///{(tmp_path / 'migration.db').as_posix()}")

    @event.listens_for(engine, "connect")
    def configure(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")
        connection.create_function("now", 0, lambda: datetime.now(UTC).isoformat())

    root = Path(__file__).resolve().parents[1]
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "alembic"))
    try:
        with engine.connect() as connection:
            config.attributes["connection"] = connection
            command.upgrade(config, "20261101_1200" if legacy_desktop else "20261110_1400")
            connection.execute(
                text(
                    "INSERT INTO courses (id, slug, title, description, level) "
                    "VALUES ('11111111111111111111111111111111', 'kept', 'Kept', 'Kept', 'A1')"
                )
            )
            if legacy_desktop:
                connection.execute(text("ALTER TABLE exercises ADD COLUMN letter_tiles JSON"))
                connection.execute(text("UPDATE alembic_version SET version_num = '20261110_1200'"))
            connection.commit()
            command.upgrade(config, "head")
            assert (
                connection.scalar(text("SELECT title FROM courses WHERE slug = 'kept'")) == "Kept"
            )
            assert connection.scalar(text("SELECT version_num FROM alembic_version")) == (
                "20261114_1200"
            )
            assert compare_metadata(MigrationContext.configure(connection), Base.metadata) == []
            assert connection.execute(text("PRAGMA foreign_key_check")).all() == []
            connection.commit()
            command.downgrade(config, "20261110_1400")
            command.upgrade(config, "head")
            assert connection.scalar(text("SELECT count(*) FROM courses")) == 1
    finally:
        engine.dispose()
