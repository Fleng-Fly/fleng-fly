"""Production entry point. Run from backend/ after installing this project."""

import logging
import sqlite3

import uvicorn

from app.core.config import get_settings


def main() -> None:
    settings = get_settings()
    try:
        # Run once in the launcher, never in an ASGI worker/lifespan.
        from app.db.prepare import main as prepare_database

        prepare_database()
    except Exception as exc:
        # SQLAlchemy exception strings can contain SQL parameters/credentials.
        cause = getattr(exc, "orig", None)
        sqlite_error = (
            getattr(cause, "sqlite_errorname", "SQLITE_ERROR")
            if isinstance(cause, sqlite3.Error)
            else "see preparation stage"
        )
        logging.getLogger("fleng").error(
            "Database preparation failed (%s, %s); Uvicorn was not started",
            type(exc).__name__,
            sqlite_error,
        )
        raise SystemExit(1) from None
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.port,
        proxy_headers=bool(settings.trusted_proxy_ips),
        forwarded_allow_ips=settings.trusted_proxy_ips,
        workers=1,
    )


if __name__ == "__main__":
    main()
