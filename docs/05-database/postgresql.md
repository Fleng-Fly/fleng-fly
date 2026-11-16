# Postgresql

Settings normalizes postgres:// and postgresql:// to postgresql+asyncpg://; explicit asyncpg URLs are supported. There is no fallback to SQLite. [Compose](../../docker-compose.yml) supplies optional PostgreSQL 16:

```sh
docker compose up -d --wait db
```

Set DATABASE_URL privately to that service before explicit Alembic upgrades; Compose alone does not change Settings. Preserve existing roles/volumes. [Retained development guide](../development.md) describes native tooling; adapt machine-specific paths.

TEST_DATABASE_URL opts into isolated PostgreSQL test schemas in a dedicated test DB; its role needs CREATE schema permission. Cleanup removes only generated test schemas. Live integration remains unverified without an actual server run. Offline SQL does not prove asyncpg connectivity, TLS, concurrency or restore behavior.

[Section index](README.md) · [Documentation home](../README.md)
