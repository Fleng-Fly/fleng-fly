"""Explicit SQLite snapshot to an empty migrated PostgreSQL schema; dry-run by default."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import Connection, DateTime, Table, create_engine, inspect, select, text, update
from sqlalchemy.engine import URL, make_url
from sqlalchemy.ext.asyncio import create_async_engine

from app.db import models  # noqa: F401
from app.db.backup import backup_sqlite
from app.db.base import Base

Rows = dict[str, list[dict[str, Any]]]
ROOT = Path(__file__).resolve().parents[2]


def check_schema(connection: Connection) -> None:
    """Reject table/revision differences and schema drift detected by Alembic."""
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "alembic"))
    heads = ScriptDirectory.from_config(config).get_heads()
    if len(heads) != 1:
        raise ValueError("Transfer requires exactly one release Alembic head")
    tables = set(inspect(connection).get_table_names())
    if tables != set(Base.metadata.tables) | {"alembic_version"}:
        raise ValueError("Schema table inventory differs from this release")
    if list(connection.scalars(text("SELECT version_num FROM alembic_version"))) != heads:
        raise ValueError("Schema must be at this release's single Alembic head")
    if compare_metadata(MigrationContext.configure(connection), Base.metadata):
        raise ValueError("Schema differs from this release's SQLAlchemy metadata")


def normalize(table: Table, row: dict[str, Any]) -> dict[str, Any]:
    # SQLite has no timezone storage. Application SQLite timestamps represent UTC.
    return {
        col.name: (value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC))
        if isinstance(col.type, DateTime) and isinstance(value := row[col.name], datetime)
        else row[col.name]
        for col in table.columns
    }


def read_rows(connection: Connection) -> Rows:
    return {
        table.name: [
            normalize(table, dict(row)) for row in connection.execute(select(table)).mappings()
        ]
        for table in Base.metadata.sorted_tables
    }


def keyed(table: Table, rows: list[dict[str, Any]]) -> dict[tuple[Any, ...], dict[str, Any]]:
    result = {tuple(row[col.name] for col in table.primary_key): row for row in rows}
    if len(result) != len(rows):
        raise ValueError(f"Duplicate primary keys in {table.name}")
    return result


def validate_rows(rows: Rows) -> None:
    """Check every declared FK, including self references, before any destination writes."""
    for table in Base.metadata.sorted_tables:
        keyed(table, rows[table.name])
        for fk in table.foreign_keys:
            parents = {row[fk.column.name] for row in rows[fk.column.table.name]}
            if any(
                row[fk.parent.name] is not None and row[fk.parent.name] not in parents
                for row in rows[table.name]
            ):
                raise ValueError(f"Foreign key violation in {table.name}.{fk.parent.name}")


def copy_rows(connection: Connection, rows: Rows) -> dict[str, int]:
    """Caller owns transaction. Never overwrite; permit exact migration seed definitions only."""
    check_schema(connection)
    validate_rows(rows)
    before = read_rows(connection)
    for table in Base.metadata.sorted_tables:
        existing = before[table.name]
        if existing and (
            table.name != "achievements" or keyed(table, existing) != keyed(table, rows[table.name])
        ):
            raise ValueError(f"Destination is occupied or conflicting: {table.name}")
    for table in Base.metadata.sorted_tables:
        if before[table.name]:
            continue
        # The only current cycle is refresh_tokens.replaced_by_id. Preserve it in phase two.
        self_links = [fk.parent for fk in table.foreign_keys if fk.column.table is table]
        for row in rows[table.name]:
            values = dict(row)
            for col in self_links:
                if not col.nullable:
                    raise ValueError("Non-null self-reference needs an explicit migration adapter")
                values[col.name] = None
            connection.execute(table.insert().values(**values))
        for row in rows[table.name]:
            links = {col.name: row[col.name] for col in self_links if row[col.name] is not None}
            if links:
                statement = update(table)
                for col in table.primary_key:
                    statement = statement.where(col == row[col.name])
                connection.execute(statement.values(**links))
    actual = read_rows(connection)
    validate_rows(actual)
    for table in Base.metadata.sorted_tables:
        if keyed(table, actual[table.name]) != keyed(table, rows[table.name]):
            raise ValueError(f"Typed row reconciliation failed: {table.name}")
    return {name: len(values) for name, values in actual.items()}


async def transfer(
    source: Path, backup: Path, destination_url: str, schema: str, *, apply: bool = False
) -> dict[str, Any]:
    url = make_url(destination_url)
    if url.drivername in {"postgres", "postgresql"}:
        url = url.set(drivername="postgresql+asyncpg")
    if url.drivername != "postgresql+asyncpg":
        raise ValueError("Destination must explicitly use PostgreSQL/asyncpg")
    if not re.fullmatch(r"[a-z_][a-z0-9_]{0,62}", schema):
        raise ValueError("Use a simple explicit PostgreSQL schema identifier")
    if backup.resolve().is_relative_to(ROOT.parent):
        raise ValueError("Backup must be outside the repository")
    backup_sqlite(source, backup)
    # SQLAlchemy Core applies UUID/JSON/bool/date processors from mapped columns.
    # Use an SQLite URI filename so mode=ro is enforced by the driver.
    source_engine = create_engine(
        URL.create(
            "sqlite", database=backup.resolve().as_uri(), query={"mode": "ro", "uri": "true"}
        )
    )
    try:
        with source_engine.connect() as connection:
            check_schema(connection)
            rows = read_rows(connection)
            validate_rows(rows)
    finally:
        source_engine.dispose()
    engine = create_async_engine(
        url,
        echo=False,
        hide_parameters=True,
        connect_args={"server_settings": {"search_path": schema}},
    )
    try:
        async with engine.connect() as connection:
            transaction = await connection.begin()
            try:
                # Lock before reading emptiness; prevents concurrent writes between check/import.
                names = sorted([*Base.metadata.tables, "alembic_version"])
                await connection.execute(
                    text(
                        "LOCK TABLE "
                        + ", ".join(f'"{name}"' for name in names)
                        + " IN ACCESS EXCLUSIVE MODE NOWAIT"
                    )
                )
                counts = await connection.run_sync(lambda sync: copy_rows(sync, rows))
                if apply:
                    await transaction.commit()
                else:
                    await transaction.rollback()
                return {"applied": apply, "row_counts": counts, "validated": True}
            except BaseException:
                await transaction.rollback()
                raise
    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--backup", required=True, type=Path, help="New private file outside repo")
    destination = parser.add_mutually_exclusive_group(required=True)
    destination.add_argument(
        "--destination-url", help="Prefer --destination-env to avoid shell history"
    )
    destination.add_argument(
        "--destination-env", help="Name of env var holding explicit target URL"
    )
    parser.add_argument("--schema", required=True)
    parser.add_argument(
        "--apply", action="store_true", help="Commit; default rehearses then rolls back"
    )
    args = parser.parse_args()
    url = os.environ.get(args.destination_env, "") if args.destination_env else args.destination_url
    if not url:
        parser.error("Explicit destination URL is missing")
    try:
        print(
            json.dumps(
                asyncio.run(transfer(args.source, args.backup, url, args.schema, apply=args.apply)),
                sort_keys=True,
            )
        )
    except Exception as exc:
        # Exceptions can contain DSNs, hashes and row values. Never print exception messages.
        parser.exit(
            1,
            f"Transfer failed ({type(exc).__name__}); transaction not approved as complete. "
            "Keep source/backup; inspect privately.\n",
        )


if __name__ == "__main__":
    main()
