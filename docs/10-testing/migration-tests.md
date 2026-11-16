# Migration tests

Use a new disposable path, from backend/:

```sh
DATABASE_URL=sqlite+aiosqlite:////tmp/fleng-doc-migrations.db .venv/bin/alembic upgrade head
DATABASE_URL=sqlite+aiosqlite:////tmp/fleng-doc-migrations.db .venv/bin/alembic current
DATABASE_URL=sqlite+aiosqlite:////tmp/fleng-doc-migrations.db .venv/bin/alembic check
```

Confirm the filename before writes. A0/vocabulary tests check data and FK preservation. `alembic heads` must show the intended single head; check/autogenerate needs live schema comparison.

Offline PostgreSQL compile (synthetic URL, no connection):

```sh
DATABASE_URL=postgresql+asyncpg://localhost/fleng_doc_sql .venv/bin/alembic upgrade head --sql > /tmp/fleng-postgresql.sql
```

This does not establish live integration. SQLite batch reflection can require a real database, so offline all-chain SQLite SQL is not equivalent.

[Section index](README.md) · [Documentation home](../README.md)
