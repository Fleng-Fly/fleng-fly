import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.errors import register_exception_handlers

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fleng")


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
    register_exception_handlers(app)
    app.include_router(api_router, prefix="/api/v1")

    return app


app = create_app()
