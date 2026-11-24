"""The Reading seed is idempotent, draft-only and never overwrites existing rows."""

import json

import pytest
from sqlalchemy import func, select

from app.db import reading_seed
from app.db.models import ReadingAnswer, ReadingArticle, ReadingCategory, ReadingQuestion
from app.modules.reading import content


async def count(db, model):
    return await db.scalar(select(func.count()).select_from(model))


async def test_seed_creates_two_draft_articles_with_valid_quizzes(db_session):
    report = await reading_seed.import_reading(db_session)
    assert (report.categories_created, report.articles_created) == (1, 2)
    articles = (await db_session.scalars(select(ReadingArticle))).all()
    assert {a.level for a in articles} == {"A0", "A1"}
    assert all(a.status == "draft" and a.published_at is None for a in articles)
    assert await count(db_session, ReadingQuestion) == 6
    assert await count(db_session, ReadingAnswer) == 18
    assert await content.list_articles(db_session) == []  # nothing visible to learners


async def test_seed_rerun_changes_nothing_and_keeps_published_state(db_session):
    await reading_seed.import_reading(db_session)
    article = await content.get_article(db_session, slug="my-day", available_only=False)
    await content.update_article(db_session, article, title="Edited by owner")
    await content.set_status(db_session, article, "published")

    report = await reading_seed.import_reading(db_session)
    assert (report.categories_created, report.articles_created, report.articles_skipped) == (
        0,
        0,
        2,
    )
    assert await count(db_session, ReadingArticle) == 2
    assert await count(db_session, ReadingCategory) == 1
    again = await content.get_article(db_session, slug="my-day")
    assert again is not None and again.title == "Edited by owner" and again.status == "published"


def test_seed_file_validation(tmp_path):
    base = json.loads(reading_seed.CONTENT.read_text(encoding="utf-8"))
    reading_seed.load()  # the shipped file is valid

    broken = json.loads(json.dumps(base))
    broken["articles"][0]["category"] = "missing"
    broken["articles"][1]["questions"][0]["correct"] = 9
    for name, data in (
        ("cat", {**base, "articles": [broken["articles"][0]]}),
        ("idx", {**base, "articles": [broken["articles"][1]]}),
    ):
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        with pytest.raises(ValueError):
            reading_seed.load(path)
