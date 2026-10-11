"""Deterministic catalog seed content.

Run with `python -m app.db.seed` (or `pnpm db:seed` from the repository root).
The seed is idempotent: courses and lessons are matched by their stable `slug`
and updated in place, so re-running never creates duplicates. It only touches
the `courses` and `lessons` tables and never modifies user data.

The content is intentionally small — enough to exercise the catalog end to end,
not a full curriculum.
"""

import asyncio
import textwrap

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Course, Lesson
from app.db.session import SessionLocal

_GREETINGS_THEORY = textwrap.dedent(
    """\
    ## Saying hello

    Use "Hello" in most situations and "Hi" with friends. In the morning you can
    say "Good morning".

    - Hello, my name is Alex.
    - Hi, I'm Sam. Nice to meet you.
    - Good morning, Mrs Brown.

    ## Introducing yourself

    To give your name, use "My name is ..." or "I'm ...". To ask, say "What's your
    name?".

    When you meet someone for the first time, add "Nice to meet you". The usual
    reply is "Nice to meet you too".

    ## Saying goodbye

    - Goodbye. See you tomorrow.
    - Bye! Have a nice day.
    - See you later.
    """
)

_TO_BE_THEORY = textwrap.dedent(
    """\
    ## The verb "to be"

    The verb "to be" has three forms in the present: am, is and are. Use "am" with
    I, "is" with he, she and it, and "are" with you, we and they.

    - I am a student.
    - She is from Spain.
    - We are ready.

    ## Short forms

    In speech we usually use short forms: I'm, you're, he's, she's, it's, we're,
    they're.

    - I'm tired.
    - They're at home.

    ## Negative sentences and questions

    Add "not" after the verb for the negative. Move the verb to the front for a
    question.

    - I am not late.
    - Are you a teacher?
    - Is she your sister?
    """
)

_NUMBERS_THEORY = textwrap.dedent(
    """\
    ## Numbers

    Learn the numbers from one to twenty first, then the tens: twenty, thirty,
    forty, fifty, sixty, seventy, eighty, ninety and one hundred.

    - 1 one, 2 two, 3 three
    - 10 ten, 11 eleven, 12 twelve
    - 20 twenty, 30 thirty

    ## Days of the week

    - Monday, Tuesday, Wednesday
    - Thursday, Friday
    - Saturday, Sunday

    ## Saying dates

    In British English the day comes before the month: "the third of May". In
    American English the month comes first: "May third".

    - My birthday is on the first of June.
    - The meeting is on Friday.
    """
)

_SMALL_TALK_THEORY = textwrap.dedent(
    """\
    ## What is small talk?

    Small talk is friendly, light conversation about everyday topics. It helps
    people feel comfortable before a real discussion.

    Good topics include the weather, your weekend, travel and food.

    ## Starting a conversation

    - It's a lovely day, isn't it?
    - How was your weekend?
    - Have you tried the new cafe?

    ## Keeping it going

    Show interest with short replies and a follow-up question.

    - Really? What did you do?
    - That sounds great. Where did you go?

    ## Ending politely

    - It was nice talking to you.
    - I should get going, but let's catch up soon.
    """
)

_ASKING_HELP_THEORY = textwrap.dedent(
    """\
    ## Polite requests

    English uses modal verbs to make requests sound polite: "could", "would" and
    "can".

    - Could you help me, please?
    - Would you mind opening the window?
    - Can I ask you a question?

    ## Please and thank you

    "Please" makes a request polite and "thank you" shows that you are grateful.
    "Would you mind ...?" is followed by an -ing form.

    - Would you mind passing the salt?
    - Thanks a lot for your help.

    ## Responding

    - Of course. No problem.
    - Sure, here you are.
    - I'm sorry, I can't right now.
    """
)

_PAST_EXPERIENCES_THEORY = textwrap.dedent(
    """\
    ## The present perfect

    Use the present perfect (have/has + past participle) for experiences when the
    exact time is not important.

    - I have visited London twice.
    - She has never tried sushi.
    - Have you ever been to Ireland?

    ## Ever and never

    Use "ever" in questions and "never" in negative statements.

    - Have you ever seen a play?
    - I have never flown before.

    ## Past simple for details

    When you give a specific time or detail, switch to the past simple.

    - I have been to Paris. I went there in 2019.
    - She has learned Spanish. She started two years ago.
    """
)

SEED_COURSES: list[dict] = [
    {
        "slug": "english-foundations",
        "title": "English Foundations",
        "description": (
            "Start from zero: greetings, the verb to be, and everyday numbers and dates."
        ),
        "level": "A1",
        "position": 1,
        "lessons": [
            {
                "slug": "greetings-and-introductions",
                "title": "Greetings and introductions",
                "summary": "Say hello, introduce yourself and say goodbye politely.",
                "estimated_minutes": 10,
                "position": 1,
                "theory": _GREETINGS_THEORY,
            },
            {
                "slug": "the-verb-to-be",
                "title": 'The verb "to be"',
                "summary": "Use am, is and are to describe people and things.",
                "estimated_minutes": 12,
                "position": 2,
                "theory": _TO_BE_THEORY,
            },
            {
                "slug": "numbers-and-days",
                "title": "Numbers, days and dates",
                "summary": "Count to one hundred and talk about the days of the week.",
                "estimated_minutes": 12,
                "position": 3,
                "theory": _NUMBERS_THEORY,
            },
        ],
    },
    {
        "slug": "everyday-conversations",
        "title": "Everyday Conversations",
        "description": (
            "Speak naturally in common situations: small talk, polite requests and "
            "past experiences."
        ),
        "level": "B1",
        "position": 2,
        "lessons": [
            {
                "slug": "small-talk",
                "title": "Small talk",
                "summary": "Start, continue and end a light conversation with confidence.",
                "estimated_minutes": 15,
                "position": 1,
                "theory": _SMALL_TALK_THEORY,
            },
            {
                "slug": "asking-for-help",
                "title": "Asking for help",
                "summary": "Make polite requests and respond to them naturally.",
                "estimated_minutes": 15,
                "position": 2,
                "theory": _ASKING_HELP_THEORY,
            },
            {
                "slug": "past-experiences",
                "title": "Talking about past experiences",
                "summary": "Use the present perfect to talk about experiences in your life.",
                "estimated_minutes": 18,
                "position": 3,
                "theory": _PAST_EXPERIENCES_THEORY,
            },
        ],
    },
]


async def seed_catalog(db: AsyncSession) -> None:
    """Create or update the seed catalog. Safe to call repeatedly."""
    for course_spec in SEED_COURSES:
        course = await db.scalar(select(Course).where(Course.slug == course_spec["slug"]))
        if course is None:
            course = Course(slug=course_spec["slug"])
            db.add(course)
        course.title = course_spec["title"]
        course.description = course_spec["description"]
        course.level = course_spec["level"]
        course.position = course_spec["position"]
        course.is_published = True
        await db.flush()

        for lesson_spec in course_spec["lessons"]:
            lesson = await db.scalar(select(Lesson).where(Lesson.slug == lesson_spec["slug"]))
            if lesson is None:
                lesson = Lesson(slug=lesson_spec["slug"])
                db.add(lesson)
            lesson.course_id = course.id
            lesson.title = lesson_spec["title"]
            lesson.summary = lesson_spec["summary"]
            lesson.theory = lesson_spec["theory"]
            lesson.position = lesson_spec["position"]
            lesson.estimated_minutes = lesson_spec["estimated_minutes"]
            lesson.is_published = True

    await db.commit()


async def main() -> None:
    async with SessionLocal() as db:
        await seed_catalog(db)
    print("Catalog seed complete.")


if __name__ == "__main__":
    asyncio.run(main())
