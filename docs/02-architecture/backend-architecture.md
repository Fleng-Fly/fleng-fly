# Backend architecture

[main.py](../../backend/app/main.py) builds the ASGI application. app/api/router.py composes ten feature routers under /api/v1. Routers parse/inject dependencies; services own transaction/learning rules; Pydantic schemas define JSON contracts. Some simple handlers query ORM objects directly, so a strict repository-layer abstraction is not present.

app/db/models.py is the ORM registry; session.py owns the async engine/session factory. app/core holds configuration, errors, body/rate limits and levels. app/services/curriculum_validation is an offline pipeline, not an HTTP service. app/preview.py is a separate local reviewer-only app factory.

Alembic owns schema changes. Preparation runs in launchers before serving rather than per-worker ASGI lifespan. Production uses one worker. See [lifecycle](../03-backend/application-lifecycle.md).

[Section index](README.md) · [Documentation home](../README.md)
