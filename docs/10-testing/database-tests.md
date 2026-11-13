# Database tests

Default fixtures create ORM tables in isolated SQLite, not necessarily through Alembic. File tests cover migrations, independent-connection locks, startup diagnostics and restart persistence. These evidence types are distinct.

TEST_DATABASE_URL selects a dedicated PostgreSQL DB; fixtures create/drop unique fleng_test_* schemas, migration tests unique migration schemas. Never use production. Without a URL PostgreSQL-specific checks skip; SQLite is not PostgreSQL proof.

```sh
cd backend
.venv/bin/pytest -q tests/test_sqlite_local.py tests/test_production_sqlite.py tests/test_stabilization.py
.venv/bin/pytest -q tests/test_postgres_migrations.py
```

The latter can explicitly skip. Live TLS/restore and provider integrations need separate evidence.

[Section index](README.md) · [Documentation home](../README.md)
