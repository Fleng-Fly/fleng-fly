"""Explicit, repeatable local demo preparation. Never changes existing accounts."""

import asyncio
import json
import os
import secrets

from sqlalchemy import select
from sqlalchemy.engine import make_url

from app.core.config import BACKEND_ROOT, get_settings
from app.db.models import Exercise, Lesson, User
from app.db.seed import seed_catalog
from app.db.session import SessionLocal, engine
from app.modules.auth.service import authenticate, register_user
from app.modules.exercises.service import get_lesson_progress, start_lesson, submit_answer

CREDENTIALS = BACKEND_ROOT / "data" / "demo-credentials.json"
ACCOUNTS = (
    ("Beginner Demo", "beginner.demo@example.com", ()),
    ("Active Demo", "active.demo@example.com", ("greetings-and-introductions:1",)),
    (
        "Advanced Demo",
        "advanced.demo@example.com",
        (
            "greetings-and-introductions:3",
            "the-verb-to-be:3",
            "numbers-and-days:3",
            "small-talk:3",
        ),
    ),
)


def save_credentials(credentials: dict[str, str]) -> None:
    CREDENTIALS.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(CREDENTIALS, os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o600)
    os.fchmod(descriptor, 0o600)
    with os.fdopen(descriptor, "w") as file:
        file.write(json.dumps(credentials, indent=2) + "\n")


def correct_answer(exercise: Exercise) -> tuple[str, str | None]:
    if exercise.type == "single_choice":
        return str(exercise.correct_option_id), None
    if exercise.type == "text":
        if not exercise.accepted_answers:
            raise RuntimeError(f"Missing accepted answer: {exercise.slug}")
        return str(exercise.accepted_answers[0]), None
    if exercise.type == "self_check":
        return str(exercise.model_answer), "correct"
    raise RuntimeError(f"Unsupported seed exercise: {exercise.type}")


async def main() -> None:
    settings = get_settings()
    if settings.app_env not in {"development", "demo"}:
        raise RuntimeError("Demo accounts require APP_ENV=development or APP_ENV=demo")
    if make_url(settings.database_url).get_backend_name() != "sqlite":
        raise RuntimeError("Demo accounts require the local SQLite database")
    if CREDENTIALS.exists():
        credentials = json.loads(CREDENTIALS.read_text())
    else:
        credentials = {}
    try:
        async with SessionLocal() as db:
            for _, email, _ in ACCOUNTS:
                if await db.scalar(
                    select(User.id).where(User.email == email)
                ) and not credentials.get(email):
                    raise RuntimeError(
                        f"{email} exists without local demo credentials; refusing to modify it"
                    )
            await seed_catalog(db)
            for name, email, targets in ACCOUNTS:
                existing = await db.scalar(select(User.id).where(User.email == email))
                password = credentials.get(email)
                if existing is not None and not password:
                    raise RuntimeError(
                        f"{email} exists without local demo credentials; refusing to modify it"
                    )
                if existing is None:
                    password = secrets.token_urlsafe(18)
                    user = await register_user(
                        db, email=email, password=password, display_name=name
                    )
                    credentials[email] = password
                    save_credentials(credentials)
                else:
                    authenticated = await authenticate(db, email=email, password=password)
                    if (
                        authenticated is None
                        or authenticated.profile is None
                        or authenticated.profile.display_name != name
                    ):
                        raise RuntimeError(
                            f"{email} is not the expected demo account; refusing to modify it"
                        )
                    user = authenticated
                for target in targets:
                    slug, count_text = target.rsplit(":", 1)
                    lesson = await db.scalar(select(Lesson).where(Lesson.slug == slug))
                    if lesson is None:
                        raise RuntimeError(f"Missing lesson: {slug}")
                    await start_lesson(db, user, lesson)
                    exercises = (
                        (
                            await db.execute(
                                select(Exercise)
                                .where(Exercise.lesson_id == lesson.id)
                                .order_by(Exercise.position)
                            )
                        )
                        .scalars()
                        .all()
                    )
                    for exercise in exercises[: int(count_text)]:
                        answer, self_assessment = correct_answer(exercise)
                        state = await get_lesson_progress(db, user, lesson)
                        if any(
                            s.exercise_id == exercise.id and s.completed for s in state.exercises
                        ):
                            continue
                        await submit_answer(
                            db,
                            user=user,
                            lesson=lesson,
                            exercise=exercise,
                            answer=answer,
                            self_assessment=self_assessment,
                        )
        save_credentials(credentials)
        print(f"Demo accounts ready. Credentials: {CREDENTIALS}")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
