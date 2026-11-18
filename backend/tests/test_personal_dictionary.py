"""Personal dictionary: words collected on lesson completion, across courses, with filters."""

import uuid

from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    Course,
    CourseVocabularyItem,
    Exercise,
    Lesson,
    LessonProgress,
    Profile,
    User,
    VocabularyItem,
)
from app.modules.vocabulary.service import collect_lesson_words

WORDS = "/api/v1/vocabulary"


async def _content(db: AsyncSession, slug: str, level: str, words: list[tuple[str, str]]):
    """One published course with one single-choice lesson teaching `words`."""
    course = Course(
        slug=slug, title=f"Course {slug}", description="d", level=level, is_published=True
    )
    lesson = Lesson(
        course=course,
        slug=f"{slug}-lesson",
        title=f"Lesson {slug}",
        summary="s",
        theory="t",
        position=1,
        estimated_minutes=5,
        is_published=True,
    )
    exercise = Exercise(
        lesson=lesson,
        slug=f"{slug}-q1",
        position=1,
        type="single_choice",
        prompt="Pick",
        points=2,
        options=[{"id": "a", "text": "A"}, {"id": "b", "text": "B"}],
        correct_option_id="a",
    )
    db.add_all([course, lesson, exercise])
    await db.flush()
    for word, translation in words:
        db.add(
            CourseVocabularyItem(
                course_id=course.id,
                lesson_id=lesson.id,
                word=word,
                translation=translation,
                example=f"Example with {word}.",
                pronunciation=f"/{word}/",
            )
        )
    await db.commit()
    return course, lesson, exercise


async def _learner(client: AsyncClient, email: str = "dict@example.com") -> dict[str, str]:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "correct-horse-battery", "displayName": "D"},
    )
    return {"Authorization": f"Bearer {response.json()['accessToken']}"}


async def _complete(
    client: AsyncClient, auth: dict, lesson: Lesson, exercise: Exercise, answer="a"
):
    return await client.post(
        f"/api/v1/lessons/{lesson.slug}/submit",
        json={"exerciseId": str(exercise.id), "answer": answer},
        headers=auth,
    )


async def test_completing_a_lesson_collects_its_words_once(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    _, lesson, exercise = await _content(db_session, "c1", "A1", [("cat", "кіт"), ("dog", "пес")])
    auth = await _learner(client)

    wrong = await _complete(client, auth, lesson, exercise, answer="b")
    assert wrong.json()["lesson"]["completed"] is False
    assert (await client.get(WORDS, headers=auth)).json() == []

    done = await _complete(client, auth, lesson, exercise)
    assert done.json()["lesson"]["completed"] is True
    assert done.json()["xpAwarded"] == 2
    body = (await client.get(WORDS, headers=auth)).json()
    assert [w["word"] for w in body] == ["cat", "dog"]
    cat = body[0]
    assert cat["translation"] == "кіт" and cat["example"] == "Example with cat."
    assert cat["pronunciation"] == "/cat/" and cat["source"] == "lesson"
    assert cat["courseTitle"] == "Course c1" and cat["lessonTitle"] == "Lesson c1"
    assert cat["lessonSlug"] == lesson.slug and cat["lessonId"] == str(lesson.id)

    # Repeating the lesson neither duplicates words nor re-awards XP.
    again = await _complete(client, auth, lesson, exercise)
    assert again.json()["xpAwarded"] == 0
    assert len((await client.get(WORDS, headers=auth)).json()) == 2
    assert await db_session.scalar(select(func.count()).select_from(VocabularyItem)) == 2


async def test_words_from_several_courses_share_one_dictionary_without_duplicates(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    c1, l1, e1 = await _content(db_session, "c1", "A1", [("cat", "кіт"), ("run", "бігти")])
    c2, l2, e2 = await _content(db_session, "c2", "B1", [("run", "бігти"), ("ocean", "океан")])
    auth = await _learner(client)
    await _complete(client, auth, l1, e1)
    await _complete(client, auth, l2, e2)

    words = (await client.get(WORDS, headers=auth)).json()
    assert sorted(w["word"] for w in words) == ["cat", "ocean", "run"]
    run = next(w for w in words if w["word"] == "run")
    assert run["courseId"] == str(c1.id)  # keeps the course it was first learned in

    groups = (await client.get(f"{WORDS}/groups", headers=auth)).json()
    assert groups["total"] == 3 and groups["other"] == 0
    assert [(c["slug"], c["count"]) for c in groups["courses"]] == [("c1", 2), ("c2", 1)]
    assert groups["courses"][1]["lessons"][0]["slug"] == l2.slug

    by_course = await client.get(WORDS, params={"courseId": str(c2.id)}, headers=auth)
    assert [w["word"] for w in by_course.json()] == ["ocean"]
    assert by_course.headers["x-total-count"] == "1"
    by_lesson = await client.get(WORDS, params={"lessonId": str(l1.id)}, headers=auth)
    assert sorted(w["word"] for w in by_lesson.json()) == ["cat", "run"]


async def test_search_matches_word_or_translation_in_any_case(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    _, lesson, exercise = await _content(
        db_session, "c1", "A1", [("cat", "Кіт"), ("category", "категорія"), ("dog", "пес")]
    )
    auth = await _learner(client)
    await _complete(client, auth, lesson, exercise)

    async def search(text: str) -> list[str]:
        response = await client.get(WORDS, params={"q": text}, headers=auth)
        assert response.headers["x-total-count"] == str(len(response.json()))
        return sorted(w["word"] for w in response.json())

    assert await search("CAT") == ["cat", "category"]
    assert await search("кіт") == ["cat"]  # stored as "Кіт"
    assert await search("ПЕС") == ["dog"]
    assert await search("100%_") == []  # wildcards are literal
    paged = await client.get(WORDS, params={"limit": 1, "offset": 1}, headers=auth)
    assert len(paged.json()) == 1 and paged.headers["x-total-count"] == "3"


async def test_existing_manual_words_are_kept_and_not_duplicated(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    _, lesson, exercise = await _content(db_session, "c1", "A1", [("cat", "кіт"), ("dog", "пес")])
    auth = await _learner(client)
    manual = await client.post(
        WORDS, headers=auth, json={"word": "Cat", "translation": "мій кіт", "example": "Mine."}
    )
    assert manual.status_code == 201
    await client.patch(f"{WORDS}/{manual.json()['id']}", headers=auth, json={"learned": True})

    await _complete(client, auth, lesson, exercise)
    words = {w["word"]: w for w in (await client.get(WORDS, headers=auth)).json()}
    assert set(words) == {"cat", "dog"}
    assert words["cat"]["translation"] == "мій кіт"  # the learner's own entry wins
    assert words["cat"]["source"] == "manual" and words["cat"]["learned"] is True
    stats = (await client.get(f"{WORDS}/stats", headers=auth)).json()
    assert stats["totalWords"] == 2 and stats["wordsLearned"] == 1


async def test_lessons_completed_before_the_feature_are_backfilled_on_view(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    _, lesson, _ = await _content(db_session, "c1", "A1", [("cat", "кіт")])
    auth = await _learner(client)
    user_id = await db_session.scalar(select(User.id))
    db_session.add(LessonProgress(user_id=user_id, lesson_id=lesson.id, status="completed"))
    await db_session.commit()

    assert [w["word"] for w in (await client.get(WORDS, headers=auth)).json()] == ["cat"]
    assert len((await client.get(WORDS, headers=auth)).json()) == 1


async def test_collection_is_owned_and_safe_to_repeat(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    _, lesson, exercise = await _content(db_session, "c1", "A1", [("cat", "кіт")])
    first = await _learner(client)
    second = await _learner(client, "second@example.com")
    await _complete(client, first, lesson, exercise)
    assert (await client.get(WORDS, headers=second)).json() == []

    user_id = await db_session.scalar(
        select(Profile.user_id).join(User).where(User.email == "dict@example.com")
    )
    assert user_id is not None
    assert await collect_lesson_words(db_session, user_id, lesson.id) == 0
    assert await collect_lesson_words(db_session, uuid.uuid4(), lesson.id) == 0


async def test_review_updates_scheduling_state(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    auth = await _learner(client)
    word = await client.post(WORDS, headers=auth, json={"word": "sun", "translation": "сонце"})
    item_id = word.json()["id"]
    await client.post(f"{WORDS}/{item_id}/review", headers=auth, json={"remembered": True})
    await client.post(f"{WORDS}/{item_id}/review", headers=auth, json={"remembered": True})
    item = await db_session.get(VocabularyItem, uuid.UUID(item_id))
    assert item is not None
    await db_session.refresh(item)
    assert (item.repetitions, item.interval_days) == (2, 7)
    assert item.last_reviewed_at is not None
    await client.post(f"{WORDS}/{item_id}/review", headers=auth, json={"remembered": False})
    await db_session.refresh(item)
    assert (item.repetitions, item.interval_days, item.learned) == (0, 1, False)


async def test_curriculum_import_links_every_word_to_the_lesson_that_teaches_it(
    db_session: AsyncSession,
) -> None:
    from app.db.curriculum import import_curriculum, load_curriculum, stable_id

    content = load_curriculum()
    report = await import_curriculum(db_session, content, apply=True)
    assert report["linked_words"] == report["words"]
    assert (
        await db_session.scalar(
            select(func.count())
            .select_from(CourseVocabularyItem)
            .where(CourseVocabularyItem.lesson_id.is_(None))
        )
        == 0
    )
    first = content.courses[0].lessons[0]
    linked = set(
        await db_session.scalars(
            select(CourseVocabularyItem.word).where(
                CourseVocabularyItem.lesson_id == stable_id("lesson", first.slug)
            )
        )
    )
    assert linked == {w.word for w in first.vocabulary}
    # Re-running is a no-op and never re-links.
    assert (await import_curriculum(db_session, content, apply=True))["linked_words"] == 0
