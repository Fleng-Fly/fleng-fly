"""Idempotent demo seed for Reading (separate command; never run at startup).

    python -m app.db.reading_seed

Creates the categories and articles in `content/reading-seed.json` that do not exist yet.
Articles are always created as **drafts**: nothing is published automatically, an owner
publishes after review. Rows that already exist (by slug) are left untouched, so a rerun
never overwrites edited or published content or changes a status.
"""

import asyncio
import json
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ReadingArticle, ReadingCategory
from app.modules.reading import content
from app.modules.reading.content import AnswerInput, QuestionInput

CONTENT = Path(__file__).with_name("content") / "reading-seed.json"


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class SeedCategory(_Strict):
    slug: str
    title: str
    description: str = ""
    position: int = 0


class SeedQuestion(_Strict):
    prompt: str
    answers: list[str] = Field(min_length=2, max_length=6)
    correct: int
    explanation: str | None = None
    points: int = 1

    @model_validator(mode="after")
    def _correct_in_range(self) -> "SeedQuestion":
        if not 0 <= self.correct < len(self.answers):
            raise ValueError("correct must index an answer")
        return self


class SeedArticle(_Strict):
    slug: str
    category: str
    level: str
    title: str
    description: str
    content: str
    questions: list[SeedQuestion] = Field(default_factory=list)


class SeedFile(_Strict):
    categories: list[SeedCategory]
    articles: list[SeedArticle]

    @model_validator(mode="after")
    def _known_categories(self) -> "SeedFile":
        known = {c.slug for c in self.categories}
        for article in self.articles:
            if article.category not in known:
                raise ValueError(f"unknown category {article.category!r}")
        return self


@dataclass
class SeedReport:
    categories_created: int = 0
    articles_created: int = 0
    articles_skipped: int = 0


def load(path: Path = CONTENT) -> SeedFile:
    return SeedFile.model_validate(json.loads(path.read_text(encoding="utf-8")))


async def import_reading(db: AsyncSession, path: Path = CONTENT) -> SeedReport:
    """Create missing categories and draft articles; leave existing rows alone."""
    data = load(path)
    report = SeedReport()
    categories: dict[str, ReadingCategory] = {}
    for spec in data.categories:
        category = await db.scalar(select(ReadingCategory).where(ReadingCategory.slug == spec.slug))
        if category is None:
            category = await content.create_category(
                db,
                slug=spec.slug,
                title=spec.title,
                description=spec.description,
                position=spec.position,
            )
            report.categories_created += 1
        categories[spec.slug] = category
    for art in data.articles:
        if await db.scalar(select(ReadingArticle.id).where(ReadingArticle.slug == art.slug)):
            report.articles_skipped += 1
            continue
        await content.create_article(
            db,
            category_id=categories[art.category].id,
            slug=art.slug,
            title=art.title,
            description=art.description,
            content=art.content,
            level=art.level,
            questions=[
                QuestionInput(
                    prompt=q.prompt,
                    answers=[AnswerInput(a, i == q.correct) for i, a in enumerate(q.answers)],
                    explanation=q.explanation,
                    points=q.points,
                )
                for q in art.questions
            ],
        )
        report.articles_created += 1
    return report


async def main() -> None:
    from app.db.session import SessionLocal

    async with SessionLocal() as db:
        print(await import_reading(db))


if __name__ == "__main__":
    asyncio.run(main())
