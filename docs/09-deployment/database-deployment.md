# Database deployment

PostgreSQL is the documented durable deployment option, but actual backup/storage/TLS guarantees come from the operator/provider. Set DATABASE_URL privately and apply `alembic upgrade head` from backend/ before startup. No automatic PostgreSQL seed exists; production catalog changes require a reviewed procedure.

SQLite startup probes access, migrates/checks schema and seeds only an empty catalog. It cannot recover learners after disk replacement. Durable volume usage needs an absolute writable filename and one launcher; validate consistent backup/restore.

Back up before migration, coordinate one maintenance owner, record current/head and check representative writes afterward. Code rollback may not support newer schema. A0 downgrade refuses A0 rows; destructive downgrade/reset is not routine rollback. Live PostgreSQL and production restore were not verified here.

[Section index](README.md) · [Documentation home](../README.md)
