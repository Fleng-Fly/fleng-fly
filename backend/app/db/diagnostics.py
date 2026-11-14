"""Allowlisted database diagnostics: never log SQL, parameters or raw exceptions."""

import asyncio
import json
import logging
import os
import sqlite3
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.config import BACKEND_ROOT, get_settings
from app.db import models  # noqa: F401 (register expected schema)
from app.db.base import Base


def error_details(exc: Exception) -> dict[str, str | int | None]:
    """Classify only known SQLite failures; even orig may contain private values."""
    cause = getattr(exc, "orig", exc)
    details: dict[str, str | int | None] = {"exception": type(exc).__name__}
    if not isinstance(cause, sqlite3.Error):
        return details
    code = getattr(cause, "sqlite_errorcode", None)
    details["sqlite_code"] = code if isinstance(code, int) else None
    name = getattr(cause, "sqlite_errorname", None)
    details["sqlite_name"] = (
        name
        if isinstance(name, str)
        and name.startswith("SQLITE_")
        and isinstance(getattr(sqlite3, name, None), int)
        else "unknown"
    )
    message = str(cause).lower()
    reason = "other_sqlite_error"
    for fragment, category in (
        ("no such table:", "missing_table"),
        ("no such column:", "missing_column"),
        ("has no column named", "missing_column"),
        ("no such function:", "missing_function"),
        ("readonly", "readonly"),
        ("read-only", "readonly"),
        ("database is locked", "locked"),
        ("database table is locked", "locked"),
        ("unable to open database file", "cannot_open"),
        ("disk is full", "disk_full"),
        ("disk i/o error", "io_error"),
        ("syntax error", "sql_syntax"),
    ):
        if fragment in message:
            reason = category
            break
    details["reason"] = reason
    if reason == "missing_table":
        # Log an object name only when it belongs to the application's schema.
        table = message.partition("no such table:")[2].strip()
        if table in Base.metadata.tables:
            details["table"] = table
    return details


async def sqlite_snapshot(engine: AsyncEngine) -> dict:
    """Inspect the actual app connection, only schema/configuration, never rows."""
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    scripts = ScriptDirectory.from_config(config)
    known_revisions = {revision.revision for revision in scripts.walk_revisions()}
    async with engine.connect() as connection:
        databases = (await connection.execute(text("PRAGMA database_list"))).all()
        actual_path = next(row[2] for row in databases if row[1] == "main")
        expected_path = engine.url.database
        tables = await connection.run_sync(lambda conn: inspect(conn).get_table_names())
        missing_tables = sorted(set(Base.metadata.tables) - set(tables))
        missing_columns = {}
        for name, table in Base.metadata.tables.items():
            if name in tables:
                columns = await connection.run_sync(
                    lambda conn, table_name: inspect(conn).get_columns(table_name), name
                )
                missing = sorted(set(table.columns.keys()) - {col["name"] for col in columns})
                if missing:
                    missing_columns[name] = missing
        revisions = (
            set(
                (
                    await connection.execute(text("SELECT version_num FROM alembic_version"))
                ).scalars()
            )
            if "alembic_version" in tables
            else set()
        )
        version = await connection.scalar(text("SELECT sqlite_version()"))
        return {
            "database_path": actual_path,
            "engine_path_matches": bool(
                actual_path
                and expected_path
                and Path(actual_path).resolve() == Path(expected_path).resolve()
            ),
            "settings_match_engine": engine.url.render_as_string(hide_password=False)
            == get_settings().database_url,
            "file_writable": os.access(actual_path, os.W_OK) if actual_path else None,
            "directory_writable": os.access(str(Path(actual_path).parent), os.W_OK)
            if actual_path
            else None,
            "sqlite_version": version,
            "returning_supported": tuple(map(int, version.split("."))) >= (3, 35, 0),
            "foreign_keys": await connection.scalar(text("PRAGMA foreign_keys")),
            "journal_mode": await connection.scalar(text("PRAGMA journal_mode")),
            "busy_timeout_ms": await connection.scalar(text("PRAGMA busy_timeout")),
            "expected_table_count": len(Base.metadata.tables),
            "missing_tables": missing_tables,
            "missing_columns": missing_columns,
            "revisions": sorted(revisions & known_revisions),
            "unknown_revision": bool(revisions - known_revisions),
            "at_head": revisions == set(scripts.get_heads()),
        }


async def log_sqlite_snapshot(engine: AsyncEngine, stage: str) -> None:
    if engine.dialect.name == "sqlite":
        logging.getLogger("fleng").info(
            "SQLite diagnostics stage=%s %s", stage, json.dumps(await sqlite_snapshot(engine))
        )


def main() -> None:
    """Render shell command. Refuse absent files; never migrate/seed or dump rows."""
    from sqlalchemy.engine import make_url

    url = make_url(get_settings().database_url)
    if url.get_backend_name() != "sqlite" or not url.database or not Path(url.database).is_file():
        print("SQLite diagnostics require an existing SQLite file")
        raise SystemExit(1)

    from app.db.session import engine

    async def report() -> None:
        try:
            print(json.dumps(await sqlite_snapshot(engine)), flush=True)
        finally:
            await engine.dispose()

    try:
        asyncio.run(report())
    except Exception as exc:
        print(json.dumps(error_details(exc)), flush=True)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
