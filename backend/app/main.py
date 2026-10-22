import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.body_limit import BodyLimitMiddleware
from app.core.config import get_settings
from app.core.errors import register_exception_handlers

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fleng")

# backend/app/main.py -> backend/app -> backend -> repository root
_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_FRONTEND_DIR = _REPO_ROOT / "frontend"


def _resolve_frontend_dir(configured: str | None) -> Path | None:
    """Return the static frontend directory, or `None` when it is absent.

    The frontend is plain HTML/CSS/JavaScript with no build step, so it can be
    served directly. Returning `None` keeps the API usable (and tests importable)
    when the directory is missing.
    """
    directory = Path(configured).expanduser() if configured else _DEFAULT_FRONTEND_DIR
    return directory if directory.is_dir() else None


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    logger.info("Fleng API starting (env=%s, port=%s)", settings.app_env, settings.port)
    yield
    logger.info("Fleng API stopped")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Fleng API", version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(BodyLimitMiddleware, max_bytes=settings.http_max_body_bytes)
    register_exception_handlers(app)
    app.include_router(api_router, prefix="/api/v1")

    # Keep unknown `/api/*` paths on the JSON error envelope: without this they
    # would fall through to the static mount below and return a plain-text 404.
    # Registered after the real routes, so it only catches unmatched API paths.
    @app.api_route(
        "/api/{_path:path}",
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
        include_in_schema=False,
    )
    async def _api_not_found(_path: str) -> None:
        raise HTTPException(status_code=404, detail="Not found")

    # Mounted last so /api/v1 and the auto-generated docs take precedence. The
    # static frontend is served from the same origin as the API, which keeps the
    # HttpOnly refresh cookie first-party and removes the need for CORS.
    frontend_dir = _resolve_frontend_dir(settings.frontend_dir)
    if frontend_dir is not None:
        app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
        logger.info("Serving static frontend from %s", frontend_dir)

    return app


app = create_app()
