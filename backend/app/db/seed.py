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

from app.core.config import get_settings
from app.db.models import Course, Exercise, Lesson
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

# Exercises keyed by their lesson's slug. Option ids are local to an exercise.
SEED_EXERCISES: dict[str, list[dict]] = {
    "greetings-and-introductions": [
        {
            "slug": "greetings-and-introductions-q1",
            "position": 1,
            "type": "single_choice",
            "prompt": "Complete the greeting: '___ , my name is Alex.'",
            "options": [
                {"id": "a", "text": "Hello"},
                {"id": "b", "text": "Goodbye"},
                {"id": "c", "text": "Sorry"},
            ],
            "correct_option_id": "a",
            "explanation": "Use 'Hello' to greet someone.",
        },
        {
            "slug": "greetings-and-introductions-q2",
            "position": 2,
            "type": "text",
            "prompt": "How do you usually reply to 'Nice to meet you'?",
            "accepted_answers": ["nice to meet you too", "nice to meet you as well"],
            "explanation": "A common reply is 'Nice to meet you too.'",
        },
        {
            "slug": "greetings-and-introductions-q3",
            "position": 3,
            "type": "self_check",
            "prompt": "Write a greeting you would use in the morning.",
            "model_answer": "Good morning!",
            "explanation": "'Good morning' is used before midday.",
        },
    ],
    "the-verb-to-be": [
        {
            "slug": "the-verb-to-be-q1",
            "position": 1,
            "type": "single_choice",
            "prompt": "She ___ from Spain.",
            "options": [
                {"id": "a", "text": "am"},
                {"id": "b", "text": "is"},
                {"id": "c", "text": "are"},
            ],
            "correct_option_id": "b",
            "explanation": "Use 'is' with she, he and it.",
        },
        {
            "slug": "the-verb-to-be-q2",
            "position": 2,
            "type": "text",
            "prompt": "Write the short form of 'I am'.",
            "accepted_answers": ["i'm", "im"],
            "explanation": "The short form is I'm.",
        },
        {
            "slug": "the-verb-to-be-q3",
            "position": 3,
            "type": "self_check",
            "prompt": "Write one sentence about yourself using 'to be'.",
            "model_answer": "I am a student.",
            "explanation": "Use am / is / are to describe yourself.",
        },
    ],
    "numbers-and-days": [
        {
            "slug": "numbers-and-days-q1",
            "position": 1,
            "type": "single_choice",
            "prompt": "Which day comes after Tuesday?",
            "options": [
                {"id": "a", "text": "Monday"},
                {"id": "b", "text": "Wednesday"},
                {"id": "c", "text": "Sunday"},
            ],
            "correct_option_id": "b",
            "explanation": "The week runs Monday, Tuesday, Wednesday.",
        },
        {
            "slug": "numbers-and-days-q2",
            "position": 2,
            "type": "text",
            "prompt": "Write the number 12 as a word.",
            "accepted_answers": ["twelve"],
            "explanation": "12 is written 'twelve'.",
        },
        {
            "slug": "numbers-and-days-q3",
            "position": 3,
            "type": "self_check",
            "prompt": "Write today's date in English.",
            "model_answer": "It is the eleventh of October.",
            "explanation": "In British English the day comes before the month.",
        },
    ],
    "small-talk": [
        {
            "slug": "small-talk-q1",
            "position": 1,
            "type": "single_choice",
            "prompt": "Which is a good topic for small talk?",
            "options": [
                {"id": "a", "text": "Your salary"},
                {"id": "b", "text": "The weather"},
                {"id": "c", "text": "Someone's age"},
            ],
            "correct_option_id": "b",
            "explanation": "Weather and weekends are safe, friendly topics.",
        },
        {
            "slug": "small-talk-q2",
            "position": 2,
            "type": "text",
            "prompt": "Complete: 'How was your ___?' (the two days off work)",
            "accepted_answers": ["weekend"],
            "explanation": "The phrase is 'How was your weekend?'",
        },
        {
            "slug": "small-talk-q3",
            "position": 3,
            "type": "self_check",
            "prompt": "Write a friendly follow-up question.",
            "model_answer": "Really? What did you do?",
            "explanation": "Follow-up questions keep the conversation going.",
        },
    ],
    "asking-for-help": [
        {
            "slug": "asking-for-help-q1",
            "position": 1,
            "type": "single_choice",
            "prompt": "Which request is the most polite?",
            "options": [
                {"id": "a", "text": "Open the window."},
                {"id": "b", "text": "Could you open the window, please?"},
                {"id": "c", "text": "Open it now."},
            ],
            "correct_option_id": "b",
            "explanation": "'Could you ... please?' is a polite request.",
        },
        {
            "slug": "asking-for-help-q2",
            "position": 2,
            "type": "text",
            "prompt": "Complete: 'Would you mind ___ the salt?' (the verb 'pass')",
            "accepted_answers": ["passing"],
            "explanation": "'Would you mind' is followed by an -ing form.",
        },
        {
            "slug": "asking-for-help-q3",
            "position": 3,
            "type": "self_check",
            "prompt": "Write a polite request to borrow a pen.",
            "model_answer": "Could I borrow a pen, please?",
            "explanation": "'Could I ... please?' is a polite request.",
        },
    ],
    "past-experiences": [
        {
            "slug": "past-experiences-q1",
            "position": 1,
            "type": "single_choice",
            "prompt": "Choose the present perfect: 'I ___ visited London twice.'",
            "options": [
                {"id": "a", "text": "have"},
                {"id": "b", "text": "has"},
                {"id": "c", "text": "had"},
            ],
            "correct_option_id": "a",
            "explanation": "Use 'have' with I, you, we and they.",
        },
        {
            "slug": "past-experiences-q2",
            "position": 2,
            "type": "text",
            "prompt": "Complete: 'Have you ___ been to Ireland?'",
            "accepted_answers": ["ever"],
            "explanation": "Use 'ever' in present-perfect questions.",
        },
        {
            "slug": "past-experiences-q3",
            "position": 3,
            "type": "self_check",
            "prompt": "Write something you have never done.",
            "model_answer": "I have never flown in a plane.",
            "explanation": "Use have / has + never + past participle.",
        },
    ],
}

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
            await db.flush()

            for exercise_spec in SEED_EXERCISES.get(lesson_spec["slug"], []):
                exercise = await db.scalar(
                    select(Exercise).where(Exercise.slug == exercise_spec["slug"])
                )
                if exercise is None:
                    exercise = Exercise(slug=exercise_spec["slug"])
                    db.add(exercise)
                exercise.lesson_id = lesson.id
                exercise.position = exercise_spec["position"]
                exercise.type = exercise_spec["type"]
                exercise.prompt = exercise_spec["prompt"]
                exercise.points = exercise_spec.get("points", 1)
                exercise.options = exercise_spec.get("options")
                exercise.correct_option_id = exercise_spec.get("correct_option_id")
                exercise.accepted_answers = exercise_spec.get("accepted_answers")
                exercise.model_answer = exercise_spec.get("model_answer")
                exercise.explanation = exercise_spec.get("explanation")

    await db.commit()


async def main() -> None:
    if get_settings().is_production:
        raise RuntimeError("Demo seed is disabled in production")
    async with SessionLocal() as db:
        await seed_catalog(db)
    print("Catalog seed complete.")


if __name__ == "__main__":
    asyncio.run(main())
