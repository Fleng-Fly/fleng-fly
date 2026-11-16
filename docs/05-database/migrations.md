# Migrations

Alembic uses [env.py](../../backend/alembic/env.py), Settings.database_url and Base.metadata. From backend/:

```sh
.venv/bin/alembic heads
.venv/bin/alembic history
.venv/bin/alembic current
.venv/bin/alembic upgrade head
.venv/bin/alembic check
```

Current head: 20261114_1200 (letter tiles), following A0 20261110_1400,
vocabulary/flashcards 20261110_1200 and AI request IDs 20261101_1200.
The obsolete desktop file `20261110_1200_letter_tiles.py` must not coexist with
the vocabulary migration: its duplicate revision ID breaks graph resolution.
The current letter-tiles migration handles databases created by that desktop
fork without restamping or resetting data. Query the current checkout instead
of copying old report heads. check compares live schema with ORM; it is not offline.

Create a new migration against a disposable up-to-date development DB:

```sh
.venv/bin/alembic revision --autogenerate -m "describe schema change"
```

Review CHECK/FK changes and SQLite batch preservation. A0 migration preserves dependents while rebuilding its parent table; downgrade refuses existing A0 courses. Back up and use one maintenance owner. Do not edit applied historical migrations, stamp blindly or drop tables as repair. [Migration tests](../10-testing/migration-tests.md) distinguish PostgreSQL offline SQL from live integration.

[Section index](README.md) · [Documentation home](../README.md)
