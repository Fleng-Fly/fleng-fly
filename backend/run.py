"""Production entry point. Run from backend/ after installing this project."""

import json
import logging

import uvicorn

from app.core.config import get_settings


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("fleng")
    logger.setLevel(logging.INFO)
    settings = get_settings()
    try:
        # Run once in the launcher, never in an ASGI worker/lifespan.
        from app.db.prepare import main as prepare_database

        prepare_database()
    except Exception as exc:
        # SQLAlchemy exception strings can contain SQL parameters/credentials.
        from app.db.diagnostics import error_details

        logger.error(
            "Database preparation failed %s; Uvicorn was not started",
            json.dumps(error_details(exc)),
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
