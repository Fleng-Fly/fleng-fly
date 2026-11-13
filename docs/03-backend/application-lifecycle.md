# Application lifecycle

app.main:app is the ordinary ASGI entry point. create_app installs middleware/errors, API routers, an unknown-/api JSON fallback and finally static frontend mounting. FastAPI supplies /docs, /redoc and /openapi.json. Missing frontend is tolerated outside production; production refuses it.

Lifespan logs startup/shutdown and production SQLite diagnostics; it does not migrate/seed. scripts/dev.mjs prepares SQLite before reload-mode Uvicorn. backend/run.py prepares before one production worker, using Settings.port and explicit proxy trust. PostgreSQL migrations remain an operator release step.

app.preview:create_preview_app is a separate loopback/reviewer factory. Ordinary app construction installs no preview routes. Ten feature routers expose 42 ordinary operations; generated docs, static files, unknown-path fallback and preview overrides are outside this count.

[Section index](README.md) · [Documentation home](../README.md)
