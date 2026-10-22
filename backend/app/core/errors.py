"""Central exception handlers mapping every error to the standard envelope.

Shape (see docs/api.md):
    { "error": { code, message, statusCode, timestamp, path, details? } }
"""

import logging
from datetime import UTC, datetime

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("fleng")


class ApiError(Exception):
    """Domain/HTTP error with an explicit envelope `code`.

    Use this instead of `HTTPException` when the status alone does not carry the
    right code (e.g. `401 INVALID_CREDENTIALS` or `409 EMAIL_TAKEN`).
    """

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: object | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details
        self.headers = headers


_STATUS_CODES = {
    400: "VALIDATION_FAILED",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    409: "CONFLICT",
    422: "VALIDATION_FAILED",
    429: "TOO_MANY_REQUESTS",
    503: "SERVICE_UNAVAILABLE",
}


def _envelope(
    status_code: int,
    code: str,
    message: str,
    path: str,
    details: object | None = None,
) -> dict:
    error: dict = {
        "code": code,
        "message": message,
        "statusCode": status_code,
        "timestamp": datetime.now(UTC).isoformat(),
        "path": path,
    }
    if details is not None:
        error["details"] = details
    return {"error": error}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=jsonable_encoder(
                _envelope(exc.status_code, exc.code, exc.message, request.url.path, exc.details)
            ),
            headers=exc.headers,
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = _STATUS_CODES.get(exc.status_code, "HTTP_ERROR")
        message = exc.detail if isinstance(exc.detail, str) else "Request failed"
        return JSONResponse(
            status_code=exc.status_code,
            content=jsonable_encoder(_envelope(exc.status_code, code, message, request.url.path)),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=jsonable_encoder(
                _envelope(
                    422,
                    "VALIDATION_FAILED",
                    "Validation failed",
                    request.url.path,
                    details=[
                        {
                            key: value
                            for key, value in error.items()
                            if key in {"type", "loc", "msg"}
                        }
                        for error in exc.errors()
                    ],
                )
            ),
        )

    @app.exception_handler(SQLAlchemyError)
    @app.exception_handler(OSError)
    async def database_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        # asyncpg surfaces an unreachable database as a raw OSError
        # (ConnectionRefusedError); SQLAlchemy surfaces query-level failures as
        # SQLAlchemyError. Both mean "database unavailable" for this API.
        logger.error(
            "Database error on %s %s (%s)", request.method, request.url.path, type(exc).__name__
        )
        return JSONResponse(
            status_code=503,
            content=_envelope(
                503, "DATABASE_UNAVAILABLE", "Database is unavailable", request.url.path
            ),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content=_envelope(500, "INTERNAL_ERROR", "Internal server error", request.url.path),
        )
