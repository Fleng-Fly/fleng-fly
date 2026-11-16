# Sqlite

SQLite+aiosqlite is the local default; relative filenames resolve under backend/. Every shared-engine connection enables foreign_keys, uses a 30-second lock timeout and registers now() for migration defaults. File parent directories are created. Learner locking/transactions do not remove SQLite's single-writer contention limit.

app.db.prepare probes write access, upgrades Alembic, validates mapped schema and seeds only an empty catalog before serving. In-memory production preparation is rejected. Process restarts preserve data only if the same file remains; ephemeral hosting replacement loses it.

Settings has a verified explicit async-memory normalization defect: sqlite+aiosqlite:///:memory: becomes a duplicated driver. Plain sqlite:///:memory: works for Settings inspection. Direct SQLAlchemy test engines are a different path. No behavior fix is included here.

Use disposable absolute paths for migration/tests/preview and never an uncertain production path. [Integrity](data-integrity.md) covers preservation boundaries.

[Section index](README.md) · [Documentation home](../README.md)
