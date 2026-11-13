"""Feature migration preserves existing vocabulary and supports SQLite rollback."""

import uuid
from pathlib import Path

from alembic.config import Config
from sqlalchemy import create_engine, text

from alembic import command


def test_vocabulary_migration_preserves_personal_words(tmp_path):
    root = Path(__file__).resolve().parents[1]
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "alembic"))
    engine = create_engine(f"sqlite:///{tmp_path / 'migration.db'}")
    user_id, word_id = uuid.uuid4().hex, uuid.uuid4().hex
    with engine.connect() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "20261101_1200")
        connection.execute(
            text(
                "INSERT INTO users (id, email, password_hash, created_at, updated_at) "
                "VALUES (:id, 'test@example.com', 'test', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
            ),
            {"id": user_id},
        )
        connection.execute(
            text(
                "INSERT INTO vocabulary_items "
                "(id, user_id, word, translation, example, learned, due_at, created_at) "
                "VALUES (:id, :owner, 'existing', 'translation', '', false, "
                "CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
            ),
            {"id": word_id, "owner": user_id},
        )
        for target in ["head", "20261101_1200", "head"]:
            connection.commit()
            if target == "head":
                command.upgrade(config, target)
            else:
                command.downgrade(config, target)
            assert connection.scalar(text("SELECT id FROM vocabulary_items")) == word_id
        command.check(config)
    engine.dispose()
