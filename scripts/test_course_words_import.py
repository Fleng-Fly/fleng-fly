"""Run without FastAPI or an async database driver: real SQLAlchemy SQLite writes.
The asynchronous production function is exercised through a synchronous test adapter.
Synthetic entries are used only for the capacity check and never shipped as catalog data.
Run: python scripts/test_course_words_import.py
"""
import asyncio
import sys
import tempfile
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import Session
from app.db.course_words_import import CONTENT, LEVELS, TARGET, Entry, import_course_words, normalize, plan_entries, read_entries
from app.db.models import Course, CourseVocabularyItem, Lesson


class Adapter:
    def __init__(self, session):
        self.session = session
    def get_bind(self):
        return self.session.get_bind()
    async def execute(self, statement):
        return self.session.execute(statement)
    async def scalars(self, statement):
        return self.session.scalars(statement)
    async def commit(self):
        self.session.commit()
    async def rollback(self):
        self.session.rollback()


async def verify():
    entries = read_entries(CONTENT)
    assert len(entries) == 581
    assert len({e.word for e in entries}) == len(entries)
    assert {e.level for e in entries} == LEVELS
    assert normalize("  WORD’S  ") == "word's"
    # Import actual bundled entries, re-run, and test strict failure before mutation.
    engine = create_engine("sqlite:///:memory:")
    Course.__table__.create(engine)
    Lesson.__table__.create(engine)
    CourseVocabularyItem.__table__.create(engine)
    with Session(engine) as s:
        ids = {level: uuid4() for level in LEVELS}
        s.add_all([Course(id=uid, slug=f"fleng-{level.lower()}", title=level, description="Test", level=level, is_published=True) for level, uid in ids.items()])
        s.commit()
        first = entries[0]
        s.add(CourseVocabularyItem(course_id=ids[first.level], word=first.word, translation="збережений переклад"))
        s.commit()
        db = Adapter(s)
        preview = await import_course_words(db)
        assert preview["added"] == 580 and preview["after"] == 581
        assert s.scalar(select(func.count()).select_from(CourseVocabularyItem)) == 1
        try:
            await import_course_words(db, require_target=True, apply=True)
        except ValueError:
            pass
        else:
            raise AssertionError("Insufficient dictionary was accepted")
        assert s.scalar(select(func.count()).select_from(CourseVocabularyItem)) == 1
        actual = await import_course_words(db, apply=True)
        assert actual["after"] == 581 and actual["added"] == 580
        assert (await import_course_words(db, apply=True))["added"] == 0
        assert s.scalar(select(CourseVocabularyItem.translation).where(CourseVocabularyItem.word == first.word)) == "збережений переклад"
        test_only = [Entry("B2", f"test-fixture-{i}", "тестовий запис") for i in range(TARGET)]
        result = await import_course_words(db, test_only, apply=True, require_target=True)
        assert result["after"] == TARGET and result["remaining"] == 0
        assert s.scalar(select(func.count()).select_from(CourseVocabularyItem)) == TARGET
        assert (await import_course_words(db, test_only, apply=True))["added"] == 0
    engine.dispose()
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp) / "bad.csv"
        path.write_text("level,word,translation\nZ9,hello,привіт\n", encoding="utf-8")
        try:
            read_entries(path)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid level accepted")
    print("PASS: 581 bundled entries; validation, preview, preservation, repeat import, strict rollback; 25,000 synthetic test records in an isolated database.")


if __name__ == "__main__":
    asyncio.run(verify())
