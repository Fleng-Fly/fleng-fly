"""Explicit SQLite online backup. Never modifies or replaces the source file."""

import argparse
import os
import sqlite3
from contextlib import closing
from pathlib import Path

from sqlalchemy.engine import make_url

from app.core.config import get_settings


def backup_sqlite(source: Path, destination: Path) -> dict[str, int]:
    source = source.resolve(strict=True)
    if not source.is_file():
        raise ValueError("Source must be an existing SQLite file")
    # Exclusive creation also refuses symlinks and an existing source/destination.
    descriptor = os.open(destination, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(descriptor)
    with closing(sqlite3.connect(source.as_uri() + "?mode=ro", uri=True)) as reader:
        with closing(sqlite3.connect(destination)) as writer:
            reader.backup(writer)
            if writer.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
                raise ValueError("Backup integrity check failed")
            if writer.execute("PRAGMA foreign_key_check").fetchall():
                raise ValueError("Backup contains foreign key violations")
            tables = writer.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ).fetchall()
            return {
                name: writer.execute(
                    'SELECT count(*) FROM "' + name.replace('"', '""') + '"'
                ).fetchone()[0]
                for (name,) in tables
            }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path, help="New private file outside the repository")
    args = parser.parse_args()
    url = make_url(get_settings().database_url)
    if url.get_backend_name() != "sqlite" or not url.database or url.database == ":memory:":
        parser.error("Use pg_dump/provider backups for PostgreSQL; SQLite needs an existing file")
    if args.destination.resolve().is_relative_to(Path(__file__).resolve().parents[3]):
        parser.error("Store backups outside the repository")
    print(backup_sqlite(Path(url.database), args.destination))


if __name__ == "__main__":
    main()
