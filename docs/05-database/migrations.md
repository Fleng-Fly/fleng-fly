# Migrations

Alembic uses [env.py](../../backend/alembic/env.py), Settings.database_url and Base.metadata. From backend/:

```sh
.venv/bin/alembic heads
.venv/bin/alembic history
.venv/bin/alembic current
.venv/bin/alembic upgrade head
.venv/bin/alembic check
```

Audited head: 20261110_1400 (A0), following vocabulary/flashcards 20261110_1200 and AI request IDs 20261101_1200. Query current checkout instead of copying old report heads. check compares live schema with ORM; it is not offline.

Create a new migration against a disposable up-to-date development DB:

```sh
.venv/bin/alembic revision --autogenerate -m "describe schema change"
```

Review CHECK/FK changes and SQLite batch preservation. A0 migration preserves dependents while rebuilding its parent table; downgrade refuses existing A0 courses. Back up and use one maintenance owner. Do not edit applied historical migrations, stamp blindly or drop tables as repair. [Migration tests](../10-testing/migration-tests.md) distinguish PostgreSQL offline SQL from live integration.

[Section index](README.md) · [Documentation home](../README.md)
