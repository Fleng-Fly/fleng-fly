"""Publish short vocabulary courses using selected words from the bundled CSV."""

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.course_words_import import CONTENT, Entry, read_entries
from app.db.curriculum import stable_id
from app.db.models import Course, CourseVocabularyItem, Exercise, Lesson

COURSES = {
    "A0": (
        ("Body and face", "cheek chin elbow knee shoulder thumb"),
        ("Things in the kitchen", "kettle knife bowl mug tray pan"),
    ),
    "A1": (
        ("Landscape and water", "hill valley meadow stream island coast"),
        ("Jobs in the community", "plumber electrician carpenter mechanic gardener firefighter"),
    ),
    "A2": (
        ("Preparing food", "whisk knead grill roast chop grate"),
        ("Visiting a theatre", "audience performance rehearsal stage costume applause"),
    ),
    "B1": (
        (
            "Working together",
            "cooperation coordination contribution conflict initiative reliability",
        ),
        (
            "Learning and feedback",
            "assessment concentration criticism distraction encouragement revision",
        ),
    ),
    "B2": (
        ("Evidence and argument", "assertion caveat criterion deduction inference premise"),
        (
            "Standards and responsibility",
            "accountability audit compliance confidentiality ethics scrutiny",
        ),
    ),
}


def _exercises(lesson_slug: str, words: list[Entry]) -> list[dict]:
    lesson_id = stable_id("lesson", lesson_slug)
    exercises = []
    for index, word in enumerate(words):
        slug = f"{lesson_slug}-{index + 1}"
        values = {
            "id": stable_id("exercise", slug),
            "lesson_id": lesson_id,
            "slug": slug,
            "position": index + 1,
            "prompt": f"Which English word means “{word.translation}”?",
            "type": "single_choice",
            "explanation": f"{word.word} — {word.translation}",
        }
        choices = [words[(index + step) % len(words)].word for step in range(1, 4)]
        correct = index % 4
        choices.insert(correct, word.word)
        values["options"] = [
            {"id": str(number), "text": choice} for number, choice in enumerate(choices)
        ]
        values["correct_option_id"] = str(correct)
        exercises.append(values)
    return exercises


async def import_vocabulary_courses(db: AsyncSession) -> None:
    entries = {(row.level, row.word): row for row in read_entries(CONTENT)}
    courses, lessons, exercises = [], [], []
    vocabulary: list[dict] = []
    for course_position, (level, topics) in enumerate(COURSES.items(), start=100):
        slug = f"fleng-vocabulary-{level.lower()}"
        course_id = stable_id("course", slug)
        courses.append(
            {
                "id": course_id,
                "slug": slug,
                "title": f"Vocabulary Workshop {level}",
                "description": (
                    f"Learn {level} vocabulary for {topics[0][0].lower()} and "
                    f"{topics[1][0].lower()}, then take the level vocabulary test."
                ),
                "level": level,
                "position": course_position,
                "is_published": True,
            }
        )
        for position, (title, terms) in enumerate(topics, start=1):
            lesson_slug = f"{slug}-lesson-{position}"
            lesson_id = stable_id("lesson", lesson_slug)
            words = [entries[level, term] for term in terms.split()]
            theory = "\n".join(f"- {word.word} — {word.translation}" for word in words)
            lessons.append(
                {
                    "id": lesson_id,
                    "course_id": course_id,
                    "slug": lesson_slug,
                    "title": title,
                    "summary": f"Study six words for {title.lower()} and check your recall.",
                    "theory": (
                        f"## {title}\n\n"
                        f"Read each pair, then try to recall the English word.\n\n{theory}"
                    ),
                    "position": position,
                    "estimated_minutes": 5,
                    "is_published": True,
                }
            )
            vocabulary.extend(
                {
                    "id": stable_id("workshop-word", f"{lesson_slug}/{word.word}"),
                    "course_id": course_id,
                    "lesson_id": lesson_id,
                    "word": word.word,
                    "translation": word.translation,
                    "example": word.example,
                }
                for word in words
            )
            exercises.extend(_exercises(lesson_slug, words))
    insert = pg_insert if db.get_bind().dialect.name == "postgresql" else sqlite_insert
    for model, rows in (
        (Course, courses),
        (Lesson, lessons),
        (CourseVocabularyItem, vocabulary),
        (Exercise, exercises),
    ):
        await db.execute(insert(model).values(rows).on_conflict_do_nothing(index_elements=["id"]))
    await db.commit()
