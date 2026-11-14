"""Loopback-only npm dev entry point: persistent local drafts, existing learner accounts."""

import asyncio
import json
import tempfile
from pathlib import Path

from sqlalchemy.engine import make_url

from app.core.config import Settings, get_settings


def validate_development_settings(settings: Settings) -> Path:
    url = make_url(settings.database_url)
    if settings.app_env != "development" or settings.render_external_url:
        raise ValueError("Draft development requires a local development environment")
    if url.drivername != "sqlite+aiosqlite" or not url.database or url.database == ":memory:":
        raise ValueError("Draft development requires a persistent local SQLite database")
    return Path(url.database)


async def import_local_drafts() -> dict:
    from app.db.curriculum import import_curriculum, load_curriculum
    from app.db.session import SessionLocal, engine

    try:
        async with SessionLocal() as session:
            return await import_curriculum(session, load_curriculum(), apply=True)
    finally:
        await engine.dispose()


def main() -> None:
    database = validate_development_settings(get_settings())
    if database.exists():
        from app.db.backup import backup_sqlite

        directory = Path(tempfile.mkdtemp(prefix="fleng-before-dev-"))
        backup = directory / "fleng.sqlite3"
        backup_sqlite(database, backup)
        print(f"Local database backup: {backup}", flush=True)
    from app.db.prepare import main as prepare_database

    prepare_database()
    result = asyncio.run(import_local_drafts())
    print("Local A0–B2 drafts ready: " + json.dumps(result), flush=True)


def create_development_app():
    validate_development_settings(get_settings())
    from fastapi import Request
    from starlette.middleware.trustedhost import TrustedHostMiddleware
    from starlette.responses import JSONResponse

    from app.main import create_app
    from app.preview import preview_router

    # Ordinary learner authentication/ownership still applies; only this local factory
    # opts into draft reads. The separate private reviewer retains its UUID restriction.
    app = create_app(local_preview_router=preview_router(None))
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "[::1]"])

    @app.middleware("http")
    async def loopback_only(request: Request, call_next):
        if request.client is None or request.client.host not in {"127.0.0.1", "::1"}:
            return JSONResponse(
                {"error": {"code": "FORBIDDEN", "message": "Local development only"}},
                status_code=403,
            )
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Fleng-Mode"] = "local-development-drafts"
        return response

    return app


if __name__ == "__main__":
    main()
