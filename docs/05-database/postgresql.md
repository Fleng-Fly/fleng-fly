# Postgresql

Settings normalizes postgres:// and postgresql:// to postgresql+asyncpg://; explicit asyncpg URLs are supported. There is no fallback to SQLite. [Compose](../../docker-compose.yml) supplies optional PostgreSQL 16:

```sh
docker compose up -d --wait db
```

Set DATABASE_URL privately to that service before startup or explicit Alembic upgrades; Compose alone does not change Settings. Preserve existing roles/volumes. [Retained development guide](../development.md) describes native tooling; adapt machine-specific paths.

TEST_DATABASE_URL opts into isolated PostgreSQL test schemas in a dedicated test DB; its role needs CREATE SCHEMA and CREATE DATABASE for startup/recovery drills. Cleanup removes only generated test schemas/databases. The durability follow-up ran an actual disposable local PostgreSQL 16.16 server.
Hosted provider connectivity/TLS/recovery remain unverified. Offline SQL does not prove asyncpg connectivity, TLS, concurrency or restore behavior.

[Section index](README.md) · [Documentation home](../README.md)

## Startup and durability

Production startup connects to the explicitly configured external database. Only
a completely empty target schema is migrated automatically. Schema creation and
owner-approved catalog loading share one transaction and advisory lock. A failed
seed/publication rolls back the initial schema too. Existing schemas at head are
checked before catalog reconciliation; older or unknown schemas are never
automatically upgraded or reset. Connection errors never fall back to SQLite.

Provider postgres URLs are normalized to asyncpg; sslmode is mapped to ssl.
Credentials remain private in Settings validation errors. Unsupported libpq
channel_binding options are rejected, not silently discarded. Keep verified TLS
for external connections and choose a provider-compatible asyncpg URI.
[Render Free setup and transfer boundary](../09-deployment/render-free-persistence.md).
