"""Add course-level EN–UK vocabulary without replacing lessons or user data.

CSV columns: level,word,translation,example. The bundled supplement is authored;
external dictionaries must be obtained and licensed by the operator. No AI or
network requests are made. The CLI previews changes unless --apply is supplied.
"""

import argparse
import asyncio
import csv
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.curriculum import stable_id
from app.db.models import Course, CourseVocabularyItem

CONTENT = Path(__file__).with_name("content") / "course-words-extra.csv"
LEVELS = {"A0", "A1", "A2", "B1", "B2"}
TARGET = 25_000


@dataclass(frozen=True)
class Entry:
    level: str
    word: str
    translation: str
    example: str = ""


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold().replace("’", "'").replace("ʼ", "'")
    return " ".join(value.split())


def read_entries(path: Path) -> list[Entry]:
    """Validate the whole file before opening a transaction; reject malformed rows."""
    result = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or []
        if len(fields) != len(set(fields)) or not {"level", "word", "translation"} <= set(fields) or set(fields) - {"level", "word", "translation", "example"}:
            raise ValueError("CSV headers must be level,word,translation[,example]")
        for row in reader:
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"CSV line {reader.line_num}: incomplete or extra fields")
            level = row["level"].strip().upper()
            word = normalize(row["word"])
            translation = row["translation"].strip()
            example = row.get("example", "").strip()
            if level not in LEVELS or not 1 <= len(word) <= 120 or not 1 <= len(translation) <= 300 or len(example) > 1000:
                raise ValueError(f"CSV line {reader.line_num}: invalid level or field length")
            if not re.search(r"[a-z]", word) or re.search(r"[а-яіїєґ]", word) or not re.search(r"[А-Яа-яІіЇїЄєҐґ]", translation):
                raise ValueError(f"CSV line {reader.line_num}: expected English word and Ukrainian translation")
            result.append(Entry(level, word, translation, example))
    return result


def plan_entries(entries: list[Entry], existing: set[str], course_ids: dict[str, UUID], target: int = TARGET) -> tuple[list[dict], dict]:
    """Keep existing words and prefer the first occurrence of new words across all levels."""
    known = {normalize(word) for word in existing}
    before = len(known)
    if target < 1:
        raise ValueError("Target must be positive")
    rows = []
    duplicates = 0
    missing = 0
    over_target = 0
    for entry in entries:
        word = normalize(entry.word)
        if word in known:
            duplicates += 1
            continue
        if entry.level not in course_ids:
            missing += 1
            continue
        if len(known) >= target:
            over_target += 1
            continue
        course_id = course_ids[entry.level]
        rows.append({
            "id": stable_id("extra-course-word", f"{course_id}/{word}"),
            "course_id": course_id,
            "lesson_id": None,
            "word": word,
            "translation": entry.translation,
            "example": entry.example,
        })
        known.add(word)
    return rows, {"before": before, "added": len(rows), "after": len(known), "duplicates": duplicates, "missing_course": missing, "over_target": over_target, "target": target, "remaining": max(0, target - len(known))}


async def import_course_words(db: AsyncSession, entries: list[Entry] | None = None, *, target: int = TARGET, apply: bool = False, require_target: bool = False) -> dict:
    entries = read_entries(CONTENT) if entries is None else entries
    courses = (await db.execute(select(Course.id, Course.level).where(Course.is_published.is_(True), Course.slug.in_([f"fleng-{level.lower()}" for level in LEVELS])))).all()
    course_ids = {level: course_id for course_id, level in courses}
    existing = set(await db.scalars(select(CourseVocabularyItem.word).join(Course).where(Course.is_published.is_(True))))
    rows, report = plan_entries(entries, existing, course_ids, target)
    if require_target and report["remaining"]:
        raise ValueError(f"Dictionary lacks {report['remaining']} distinct entries; no changes applied")
    if apply:
        insert = pg_insert if db.get_bind().dialect.name == "postgresql" else sqlite_insert
        # Small batches work on SQLite's parameter limits as well as PostgreSQL.
        try:
            for start in range(0, len(rows), 100):
                statement = insert(CourseVocabularyItem).values(rows[start:start + 100]).on_conflict_do_nothing(index_elements=[CourseVocabularyItem.course_id, CourseVocabularyItem.word])
                await db.execute(statement)
            actual = {normalize(word) for word in await db.scalars(select(CourseVocabularyItem.word).join(Course).where(Course.is_published.is_(True)))}
            report.update(after=len(actual), added=len(actual) - report["before"], remaining=max(0, target - len(actual)))
            if require_target and report["remaining"]:
                raise ValueError("Dictionary target was not reached; rolling back")
            await db.commit()
        except Exception:
            await db.rollback()
            raise
    return report


async def _main(args: argparse.Namespace) -> None:
    from app.db.session import SessionLocal, engine

    try:
        async with SessionLocal() as db:
            report = await import_course_words(db, read_entries(args.csv), target=args.target, apply=args.apply, require_target=args.require_target)
            print("APPLIED" if args.apply else "PREVIEW (no changes)", report)
    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=CONTENT)
    parser.add_argument("--target", type=int, default=TARGET)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--require-target", action="store_true", help="Reject imports that cannot reach target in this run")
    asyncio.run(_main(parser.parse_args()))


if __name__ == "__main__":
    main()
