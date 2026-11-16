"""Local curriculum-review app factory. Never used by normal/production startup.

Authentication uses the existing JWT/refresh flow. The private preview factory
restricts drafts to its freshly provisioned reviewer; the separate loopback-only
development factory reuses these routes for ordinary local learner accounts.
Publication flags remain false; grading and progress use the existing services.
"""

import json
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import JSONResponse

from app.api.deps import get_current_user
from app.core.config import Settings, get_settings
from app.core.errors import ApiError
from app.core.levels import LearningLevel
from app.db.curriculum import content_sha, load_curriculum
from app.db.models import User
from app.db.session import get_db
from app.modules.catalog import service as catalog
from app.modules.catalog.schemas import (
    CourseDetailResponse,
    CourseSummaryResponse,
    LessonDetailResponse,
)
from app.modules.exercises import service as exercises
from app.modules.exercises.schemas import (
    LessonProgressResponse,
    SubmissionRequest,
    SubmissionResultResponse,
)
from app.modules.progress import service as progress
from app.modules.progress.schemas import ProgressResponse
from app.modules.vocabulary import flashcards
from app.modules.vocabulary.schemas import CourseWordResponse

PREVIEW_DATABASE = "curriculum-preview.sqlite3"
PREVIEW_MARKER = "preview.json"
PREVIEW_KIND = "fleng-curriculum-preview-v1"


def load_marker(directory: Path) -> dict:
    directory = directory.absolute()
    if directory.is_symlink() or directory.resolve() != directory:
        raise ValueError("Preview directory must not use symlinks")
    marker = directory / PREVIEW_MARKER
    if marker.is_symlink() or (directory / PREVIEW_DATABASE).is_symlink():
        raise ValueError("Preview files must not use symlinks")
    import os

    getuid = getattr(os, "getuid", None)
    if getuid is None:
        raise ValueError("Private curriculum preview requires POSIX file permissions")
    for path in (directory, marker, directory / PREVIEW_DATABASE):
        info = path.stat()
        if info.st_uid != getuid() or info.st_mode & 0o077:
            raise ValueError("Preview files must be private and owned by this user")
    data = json.loads(marker.read_text(encoding="utf-8"))
    if data.get("kind") != PREVIEW_KIND or data.get("database") != PREVIEW_DATABASE:
        raise ValueError("Not a Fleng preview directory")
    UUID(data["reviewer_id"])
    if len(data["jwt_secret"]) < 32:
        raise ValueError("Invalid preview signing key")
    return data


def validate_preview_settings(settings: Settings) -> dict:
    if settings.app_env != "development":
        raise ValueError("Preview requires development mode; production is forbidden")
    url = make_url(settings.database_url)
    if url.drivername != "sqlite+aiosqlite" or not url.database:
        raise ValueError("Preview requires isolated file-backed SQLite")
    path = Path(url.database)
    if path.name != PREVIEW_DATABASE:
        raise ValueError("Only a prepared preview database is accepted")
    marker = load_marker(path.parent)
    if (
        settings.jwt_access_secret != marker["jwt_secret"]
        or settings.refresh_cookie_name != "fleng_curriculum_preview"
        or settings.ai_enabled
        or settings.reset_delivery != "disabled"
    ):
        raise ValueError("Use the isolated preview launcher configuration")
    if marker["curriculum_sha"] != content_sha(load_curriculum()):
        raise ValueError("Draft source changed; prepare a new preview directory")
    return marker


def preview_router(reviewer_id: UUID | None) -> APIRouter:
    async def reviewer(user: User = Depends(get_current_user)) -> User:
        if reviewer_id is not None and user.id != reviewer_id:
            raise ApiError(403, "FORBIDDEN", "Curriculum preview is restricted to its reviewer")
        return user

    router = APIRouter(tags=["local-preview"], dependencies=[Depends(reviewer)])

    @router.get("/preview/status")
    async def status():
        return {"mode": "local_draft_preview", "published": False}

    @router.get("/courses", response_model=list[CourseSummaryResponse])
    async def courses(
        level: LearningLevel | None = Query(None), db: AsyncSession = Depends(get_db)
    ):
        return await catalog.list_published_courses(db, level=level, include_drafts=True)

    @router.get("/courses/{slug}", response_model=CourseDetailResponse)
    async def course(slug: str, db: AsyncSession = Depends(get_db)):
        result = await catalog.get_published_course(db, slug, include_drafts=True)
        if result is None:
            raise ApiError(404, "NOT_FOUND", "Course not found")
        return catalog.to_course_detail(result)

    @router.get("/lessons/{slug}", response_model=LessonDetailResponse)
    async def lesson(slug: str, db: AsyncSession = Depends(get_db)):
        result = await exercises.get_lesson_or_404(db, slug, include_drafts=True)
        row, course_row = result
        return catalog.to_lesson_detail(
            row, course_row, await exercises.list_public_exercises(db, row.id)
        )

    @router.get("/lessons/{slug}/progress", response_model=LessonProgressResponse)
    async def lesson_progress(
        slug: str, user: User = Depends(reviewer), db: AsyncSession = Depends(get_db)
    ):
        row, _ = await exercises.get_lesson_or_404(db, slug, include_drafts=True)
        return await exercises.get_lesson_progress(db, user, row)

    @router.post("/lessons/{slug}/start", response_model=LessonProgressResponse)
    async def start(slug: str, user: User = Depends(reviewer), db: AsyncSession = Depends(get_db)):
        row, _ = await exercises.get_lesson_or_404(db, slug, include_drafts=True)
        return await exercises.start_lesson(db, user, row)

    @router.post("/lessons/{slug}/submit", response_model=SubmissionResultResponse)
    async def submit(
        slug: str,
        payload: SubmissionRequest,
        user: User = Depends(reviewer),
        db: AsyncSession = Depends(get_db),
    ):
        row, _ = await exercises.get_lesson_or_404(db, slug, include_drafts=True)
        exercise = await exercises.get_exercise_or_404(db, row, payload.exercise_id)
        return await exercises.submit_answer(
            db,
            user=user,
            lesson=row,
            exercise=exercise,
            answer=payload.answer,
            self_assessment=payload.self_assessment,
        )

    @router.get("/progress/me", response_model=ProgressResponse)
    async def my_progress(user: User = Depends(reviewer), db: AsyncSession = Depends(get_db)):
        return await progress.to_progress_response(
            db,
            user_id=user.id,
            progress=await progress.get_progress(db, user.id),
            xp=user.profile.xp if user.profile else 0,
            include_drafts=True,
        )

    @router.get("/vocabulary/course-words", response_model=list[CourseWordResponse])
    async def words(
        course_id: UUID | None = Query(None, alias="courseId"),
        level: LearningLevel | None = None,
        limit: int = Query(50, ge=1, le=100),
        offset: int = Query(0, ge=0),
        db: AsyncSession = Depends(get_db),
    ):
        query = await flashcards.course_query(db, course_id, level, include_drafts=True)
        return (await db.scalars(query.limit(limit).offset(offset))).all()

    return router


def create_preview_app():
    from app.main import create_app

    marker = validate_preview_settings(get_settings())
    app = create_app(local_preview_router=preview_router(UUID(marker["reviewer_id"])))
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "[::1]"])

    @app.middleware("http")
    async def loopback_only(request: Request, call_next):
        if request.client is None or request.client.host not in {"127.0.0.1", "::1"}:
            return JSONResponse(
                {"error": {"code": "FORBIDDEN", "message": "Local preview only"}}, status_code=403
            )
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Fleng-Mode"] = "local-draft-preview"
        return response

    return app
