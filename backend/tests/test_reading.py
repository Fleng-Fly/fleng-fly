"""Reading backend: authoring, progress, attempts, grading, XP, bookmarks and preferences."""

import uuid

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.db.models import (
    Achievement,
    LearningActivity,
    Profile,
    Progress,
    ReadingAnswer,
    ReadingArticle,
    ReadingAttempt,
    ReadingBookmark,
    ReadingCategory,
    ReadingQuestion,
    ReadingUserProgress,
    User,
)
from app.modules.reading import content, learning, personal
from app.modules.reading.content import AnswerInput, ArticleFilters, QuestionInput


async def make_user(db: AsyncSession, name: str = "u") -> User:
    user = User(email=f"{name}-{uuid.uuid4().hex[:6]}@example.com", password_hash="x")
    user.profile = Profile(display_name=name)
    user.progress = Progress()
    db.add(user)
    await db.commit()
    return user


def question(prompt: str = "Why?", points: int = 1, correct: int = 0) -> QuestionInput:
    return QuestionInput(
        prompt=prompt,
        points=points,
        explanation=f"Because {prompt}",
        answers=[AnswerInput(text=f"opt {i}", is_correct=i == correct) for i in range(3)],
    )


async def make_category(db: AsyncSession, slug: str = "travel", **kw) -> ReadingCategory:
    return await content.create_category(db, slug=slug, title=slug.title(), **kw)


async def make_article(
    db: AsyncSession,
    category: ReadingCategory,
    slug: str = "a-trip",
    *,
    questions: list[QuestionInput] | None = None,
    publish: bool = True,
    **kw,
) -> ReadingArticle:
    kw.setdefault("level", "A1")
    article = await content.create_article(
        db,
        category_id=category.id,
        slug=slug,
        title="A trip",
        description="Short story",
        content="We went to the sea. " * 30,
        questions=[question("Q1", 2), question("Q2", 3)] if questions is None else questions,
        **kw,
    )
    return await content.set_status(db, article, "published") if publish else article


def pick(article: ReadingArticle, *, right: bool = True) -> dict[uuid.UUID, uuid.UUID]:
    """Choose the correct (or a wrong) answer for every question."""
    return {q.id: next(a.id for a in q.answers if a.is_correct == right) for q in article.questions}


async def xp(db: AsyncSession, user: User) -> int:
    return (
        await db.scalar(
            select(Profile.xp)
            .where(Profile.user_id == user.id)
            .execution_options(populate_existing=True)
        )
    ) or 0


# --- articles, categories, relationships --------------------------------------------------


async def test_create_and_get_article_with_questions(db_session):
    category = await make_category(db_session)
    article = await make_article(db_session, category, cover_image_url="https://x.test/c.jpg")

    loaded = await content.get_article(db_session, slug="a-trip")
    assert loaded is not None and loaded.id == article.id
    assert loaded.category.slug == "travel"
    assert [q.position for q in loaded.questions] == [1, 2]
    assert [a.position for a in loaded.questions[0].answers] == [1, 2, 3]
    assert sum(a.is_correct for a in loaded.questions[0].answers) == 1
    assert loaded.status == "published" and loaded.published_at is not None
    assert loaded.cover_image_url == "https://x.test/c.jpg"
    assert await content.get_article(db_session, article_id=article.id) is not None


async def test_reading_minutes_estimated_or_explicit(db_session):
    category = await make_category(db_session)
    estimated = await make_article(db_session, category, "est", publish=False)
    explicit = await make_article(db_session, category, "exp", publish=False, reading_minutes=7)
    assert estimated.reading_minutes == 1  # 120 words at 150 wpm
    assert explicit.reading_minutes == 7
    assert content.estimate_reading_minutes("word " * 451) == 4
    assert content.estimate_reading_minutes("") == 1
    assert content.estimate_reading_minutes("w " * 1_000_000) == content.MAX_READING_MINUTES


@pytest.mark.parametrize("level", ["A0", "A1", "A2", "B1", "B2"])
async def test_valid_levels(db_session, level):
    category = await make_category(db_session)
    assert (await make_article(db_session, category, level=level)).level == level


@pytest.mark.parametrize("level", ["C1", "C2", "a1", "", "X"])
async def test_invalid_levels_rejected(db_session, level):
    category = await make_category(db_session)
    with pytest.raises(ApiError) as error:
        await make_article(db_session, category, level=level)
    assert error.value.status_code == 422


async def test_database_enforces_level_status_and_single_correct_answer(db_session):
    category = await make_category(db_session)
    article = await make_article(db_session, category)
    category_id, article_id = category.id, article.id  # rollback expires loaded objects
    db_session.add(
        ReadingArticle(
            category_id=category_id,
            slug="bad",
            title="t",
            description="d",
            content="c",
            level="C1",
            reading_minutes=1,
        )
    )
    with pytest.raises(IntegrityError):
        await db_session.flush()
    await db_session.rollback()

    first = (await content.get_article(db_session, article_id=article_id)).questions[0]
    db_session.add(ReadingAnswer(question_id=first.id, position=9, text="x", is_correct=True))
    with pytest.raises(IntegrityError):  # a second correct answer
        await db_session.flush()
    await db_session.rollback()


async def test_unique_slugs(db_session):
    category = await make_category(db_session)
    category_id = category.id  # a failed create rolls back and expires loaded objects
    with pytest.raises(ApiError) as error:
        await make_category(db_session)
    assert error.value.status_code == 409
    category = await content.get_category(db_session, category_id)
    await make_article(db_session, category)
    with pytest.raises(ApiError) as error:
        await make_article(db_session, category)
    assert error.value.status_code == 409


@pytest.mark.parametrize("slug", ["", "Bad Slug", "UPPER", "-x", "x-", "a--b", "a_b"])
async def test_invalid_slug(db_session, slug):
    with pytest.raises(ApiError):
        await content.create_category(db_session, slug=slug, title="T")


@pytest.mark.parametrize(
    "bad",
    [
        {"title": "  "},
        {"content": ""},
        {"description": "x" * 501},
        {"reading_minutes": 0},
        {"reading_minutes": 121},
        {"cover_image_url": "javascript:alert(1)"},
        {"cover_image_url": "//evil.test/x.png"},
        {"cover_image_url": "http://insecure.test/x.png"},
    ],
)
async def test_invalid_article_fields(db_session, bad):
    category = await make_category(db_session)
    args = dict(
        category_id=category.id, slug="s", title="T", description="D", content="C", level="A1"
    )
    with pytest.raises(ApiError) as error:
        await content.create_article(db_session, **{**args, **bad})
    assert error.value.status_code == 422


async def test_unknown_category_rejected(db_session):
    with pytest.raises(ApiError) as error:
        await content.create_article(
            db_session,
            category_id=uuid.uuid4(),
            slug="s",
            title="T",
            description="D",
            content="C",
            level="A1",
        )
    assert error.value.status_code == 404


@pytest.mark.parametrize(
    "bad",
    [
        QuestionInput("Q", [AnswerInput("a", True)]),  # one answer
        QuestionInput("Q", [AnswerInput("a"), AnswerInput("b")]),  # none correct
        QuestionInput("Q", [AnswerInput("a", True), AnswerInput("b", True)]),  # two correct
        QuestionInput("Q", [AnswerInput("a", True), AnswerInput("A")]),  # duplicate text
        QuestionInput("Q", [AnswerInput("a", True), AnswerInput(" ")]),  # blank answer
        QuestionInput(" ", [AnswerInput("a", True), AnswerInput("b")]),  # blank prompt
        QuestionInput("Q", [AnswerInput("a", True), AnswerInput("b")], points=0),
        QuestionInput("Q", [AnswerInput("a", True), AnswerInput("b")], points=11),
        QuestionInput("Q", [AnswerInput(str(i), i == 0) for i in range(7)]),  # too many
    ],
)
async def test_invalid_questions_rejected_and_nothing_saved(db_session, bad):
    category = await make_category(db_session)
    with pytest.raises(ApiError) as error:
        await make_article(db_session, category, questions=[question(), bad], publish=False)
    assert error.value.status_code == 422
    assert await db_session.scalar(select(func.count()).select_from(ReadingArticle)) == 0


async def test_visibility_follows_status_and_category(db_session):
    category = await make_category(db_session)
    draft = await make_article(db_session, category, "draft", publish=False)
    live = await make_article(db_session, category, "live")
    other = await make_category(db_session, "food")
    await make_article(db_session, other, "meal", level="B1")

    assert {a.slug for a in await content.list_articles(db_session)} == {"live", "meal"}
    assert await content.get_article(db_session, slug="draft") is None
    assert (await content.get_article(db_session, slug="draft", available_only=False)).id == (
        draft.id
    )

    archived = await content.set_status(db_session, live, "archived")
    assert archived.status == "archived"
    assert {a.slug for a in await content.list_articles(db_session)} == {"meal"}

    await content.update_category(db_session, other, is_active=False)
    assert await content.list_articles(db_session) == []
    assert len(await content.list_articles(db_session, ArticleFilters(available_only=False))) == 3
    assert [c.slug for c in await content.list_categories(db_session)] == ["travel"]
    assert len(await content.list_categories(db_session, active_only=False)) == 2


async def test_list_filters_and_pagination(db_session):
    travel = await make_category(db_session)
    food = await make_category(db_session, "food")
    for i, (cat, level) in enumerate([(travel, "A1"), (travel, "B1"), (food, "A1")]):
        await make_article(db_session, cat, f"art-{i}", level=level)
    only = lambda **kw: content.list_articles(db_session, ArticleFilters(**kw))  # noqa: E731
    assert len(await only(category_id=travel.id)) == 2
    assert len(await only(level="A1")) == 2
    assert len(await only(category_id=travel.id, level="B1")) == 1
    assert len(await only(limit=1)) == 1
    assert len(await only(limit=10, offset=2)) == 1
    for bad in (dict(limit=0), dict(limit=201), dict(offset=-1), dict(level="C2")):
        with pytest.raises(ApiError):
            await only(**bad)


async def test_publish_requires_valid_state_and_keeps_first_published_at(db_session):
    category = await make_category(db_session)
    article = await make_article(db_session, category, publish=False)
    assert article.published_at is None
    article = await content.set_status(db_session, article, "published")
    first = article.published_at
    article = await content.set_status(db_session, article, "draft")
    article = await content.set_status(db_session, article, "published")
    assert article.published_at == first
    with pytest.raises(ApiError):
        await content.set_status(db_session, article, "deleted")

    await content.update_category(db_session, category, is_active=False)
    hidden = await content.get_article(db_session, slug="a-trip", available_only=False)
    with pytest.raises(ApiError) as error:
        await content.set_status(db_session, hidden, "published")
    assert error.value.status_code == 409


async def test_update_article_and_replace_questions(db_session):
    category = await make_category(db_session)
    article = await make_article(db_session, category)
    moved = await make_category(db_session, "food")
    article = await content.update_article(
        db_session,
        article,
        title="New",
        level="B2",
        category_id=moved.id,
        reading_minutes=5,
        content="word " * 600,
    )
    assert (article.title, article.level, article.category.slug) == ("New", "B2", "food")
    assert article.reading_minutes == 5
    article = await content.update_article(db_session, article, content="word " * 600)
    assert article.reading_minutes == 4  # re-estimated when content changes alone
    with pytest.raises(ApiError):
        await content.update_article(db_session, article, level="C1")

    article = await content.replace_questions(db_session, article, [question("Only", 4)])
    assert [q.prompt for q in article.questions] == ["Only"]
    assert await db_session.scalar(select(func.count()).select_from(ReadingQuestion)) == 1
    assert await db_session.scalar(select(func.count()).select_from(ReadingAnswer)) == 3
    with pytest.raises(ApiError):
        await content.replace_questions(db_session, article, [QuestionInput("Q", [])])
    assert len((await content.get_article(db_session, slug="a-trip")).questions) == 1


async def test_deleting_article_cascades_but_category_is_protected(db_session):
    category = await make_category(db_session)
    article = await make_article(db_session, category)
    await db_session.delete(category)
    with pytest.raises(IntegrityError):
        await db_session.flush()
    await db_session.rollback()
    await db_session.delete(await content.get_article(db_session, slug="a-trip"))
    await db_session.commit()
    assert await db_session.scalar(select(func.count()).select_from(ReadingQuestion)) == 0
    assert await db_session.scalar(select(func.count()).select_from(ReadingAnswer)) == 0
    assert article.id


# --- progress -----------------------------------------------------------------------------


async def test_read_progress_only_grows_and_validates(db_session):
    user = await make_user(db_session)
    article = await make_article(db_session, await make_category(db_session))
    assert await learning.get_progress(db_session, user.id, article.id) is None
    progress = await learning.update_read_progress(db_session, user.id, article.id, 40)
    assert (progress.read_percent, progress.status) == (40, "in_progress")
    assert (
        await learning.update_read_progress(db_session, user.id, article.id, 10)
    ).read_percent == 40
    assert (
        await learning.update_read_progress(db_session, user.id, article.id, 75)
    ).read_percent == 75
    # 100% alone does not complete an article that has a quiz
    done = await learning.update_read_progress(db_session, user.id, article.id, 100)
    assert (done.read_percent, done.status, done.completed_at) == (100, "in_progress", None)
    for bad in (-1, 101, True, 1.5, "50"):
        with pytest.raises(ApiError):
            await learning.update_read_progress(db_session, user.id, article.id, bad)
    with pytest.raises(ApiError) as error:
        await learning.update_read_progress(db_session, user.id, uuid.uuid4(), 5)
    assert error.value.status_code == 404
    assert await db_session.scalar(select(func.count()).select_from(ReadingUserProgress)) == 1


async def test_article_without_questions_completes_at_100_once_without_xp(db_session):
    user = await make_user(db_session)
    article = await make_article(db_session, await make_category(db_session), questions=[])
    first = await learning.update_read_progress(db_session, user.id, article.id, 100)
    assert first.status == "completed" and first.completed_at is not None
    stamp = first.completed_at
    again = await learning.update_read_progress(db_session, user.id, article.id, 100)
    assert again.completed_at == stamp
    assert await xp(db_session, user) == 0
    assert await db_session.scalar(select(func.count()).select_from(LearningActivity)) == 1
    with pytest.raises(ApiError) as error:
        await learning.start_attempt(db_session, user.id, article.id)
    assert error.value.code == "NO_QUESTIONS"


async def test_hidden_articles_reject_learner_actions(db_session):
    user = await make_user(db_session)
    draft = await make_article(db_session, await make_category(db_session), publish=False)
    for call in (
        learning.update_read_progress(db_session, user.id, draft.id, 5),
        learning.start_attempt(db_session, user.id, draft.id),
        personal.add_bookmark(db_session, user.id, draft.id),
    ):
        with pytest.raises(ApiError) as error:
            await call
        assert error.value.status_code == 404


# --- attempts: save, restore, grading ------------------------------------------------------


async def test_start_restores_active_attempt_and_numbers_new_ones(db_session):
    user = await make_user(db_session)
    article = await make_article(db_session, await make_category(db_session))
    first = await learning.start_attempt(db_session, user.id, article.id)
    again = await learning.start_attempt(db_session, user.id, article.id)
    assert again.id == first.id and first.attempt_number == 1

    await learning.submit_attempt(db_session, user.id, first.id, pick(article, right=False))
    second = await learning.start_attempt(db_session, user.id, article.id)
    assert second.id != first.id and second.attempt_number == 2
    assert (await learning.get_active_attempt(db_session, user.id, article.id)).id == second.id
    assert [
        a.attempt_number for a in await learning.list_attempts(db_session, user.id, article.id)
    ] == [2, 1]


async def test_save_answers_merges_and_is_restored(db_session):
    user = await make_user(db_session)
    article = await make_article(db_session, await make_category(db_session))
    attempt = await learning.start_attempt(db_session, user.id, article.id)
    q1, q2 = article.questions
    await learning.save_answers(db_session, user.id, attempt.id, {q1.id: q1.answers[1].id})
    await learning.save_answers(db_session, user.id, attempt.id, {q2.id: q2.answers[0].id})
    await learning.save_answers(
        db_session, user.id, attempt.id, {q1.id: q1.answers[0].id}
    )  # change
    restored = await learning.get_attempt(db_session, user.id, attempt.id)
    assert restored.answers == {
        str(q1.id): str(q1.answers[0].id),
        str(q2.id): str(q2.answers[0].id),
    }
    assert restored.status == "in_progress" and restored.result is None


async def test_save_answers_validation(db_session):
    user = await make_user(db_session)
    cat = await make_category(db_session)
    article = await make_article(db_session, cat)
    foreign = await make_article(db_session, cat, "other")
    attempt = await learning.start_attempt(db_session, user.id, article.id)
    q1 = article.questions[0]
    for bad in (
        {uuid.uuid4(): q1.answers[0].id},  # unknown question
        {q1.id: uuid.uuid4()},  # unknown answer
        {q1.id: article.questions[1].answers[0].id},  # answer of another question
        {foreign.questions[0].id: foreign.questions[0].answers[0].id},  # other article
    ):
        with pytest.raises(ApiError) as error:
            await learning.save_answers(db_session, user.id, attempt.id, bad)
        assert error.value.code == "INVALID_ANSWER"
    assert (await learning.get_attempt(db_session, user.id, attempt.id)).answers == {}


async def test_grading_scores_and_threshold(db_session):
    user = await make_user(db_session)
    article = await make_article(
        db_session,
        await make_category(db_session),
        questions=[question("A", 7), question("B", 3)],
    )
    # 7/10 = 70% -> passes; only the 3-point question right -> 30% -> fails
    attempt = await learning.start_attempt(db_session, user.id, article.id)
    q1, q2 = article.questions
    right1 = {q1.id: next(a.id for a in q1.answers if a.is_correct)}
    wrong2 = {q2.id: next(a.id for a in q2.answers if not a.is_correct)}
    done = await learning.submit_attempt(db_session, user.id, attempt.id, {**right1, **wrong2})
    assert (done.points_earned, done.points_possible, done.score_percent) == (7, 10, 70)
    assert done.passed is True and done.status == "submitted" and done.submitted_at

    low = await learning.start_attempt(db_session, user.id, article.id)
    done = await learning.submit_attempt(
        db_session,
        user.id,
        low.id,
        {q2.id: next(a.id for a in q2.answers if a.is_correct)},
    )
    assert (done.score_percent, done.passed) == (30, False)
    entry = {i["question_id"]: i for i in done.result["questions"]}
    assert entry[str(q1.id)]["selected_answer_id"] is None  # unanswered scores 0
    assert entry[str(q2.id)]["is_correct"] is True
    assert entry[str(q1.id)]["explanation"] == "Because A"


async def test_two_of_three_correct_is_66_percent_and_fails(db_session):
    user = await make_user(db_session)
    article = await make_article(
        db_session, await make_category(db_session), questions=[question(f"Q{i}") for i in range(3)]
    )
    attempt = await learning.start_attempt(db_session, user.id, article.id)
    answers = pick(article)
    answers[article.questions[2].id] = next(
        a.id for a in article.questions[2].answers if not a.is_correct
    )
    done = await learning.submit_attempt(db_session, user.id, attempt.id, answers)
    assert (done.score_percent, done.passed, done.xp_awarded) == (66, False, 0)


async def test_attempt_result_is_a_frozen_snapshot(db_session):
    user = await make_user(db_session)
    article = await make_article(db_session, await make_category(db_session))
    attempt = await learning.start_attempt(db_session, user.id, article.id)
    done = await learning.submit_attempt(db_session, user.id, attempt.id, pick(article))
    before = dict(done.result)
    await content.replace_questions(db_session, article, [question("Totally new", 9)])
    again = await learning.get_attempt(db_session, user.id, attempt.id)
    assert again.result == before and again.points_possible == 5


async def test_attempts_are_private_to_their_owner(db_session):
    owner, other = await make_user(db_session, "a"), await make_user(db_session, "b")
    article = await make_article(db_session, await make_category(db_session))
    attempt = await learning.start_attempt(db_session, owner.id, article.id)
    for call in (
        learning.get_attempt(db_session, other.id, attempt.id),
        learning.save_answers(db_session, other.id, attempt.id, {}),
        learning.submit_attempt(db_session, other.id, attempt.id, {}),
    ):
        with pytest.raises(ApiError) as error:
            await call
        assert error.value.status_code == 404
    other_attempt = await learning.start_attempt(db_session, other.id, article.id)
    assert other_attempt.id != attempt.id and other_attempt.attempt_number == 1


async def test_cannot_save_into_submitted_attempt(db_session):
    user = await make_user(db_session)
    article = await make_article(db_session, await make_category(db_session))
    attempt = await learning.start_attempt(db_session, user.id, article.id)
    await learning.submit_attempt(db_session, user.id, attempt.id, pick(article, right=False))
    with pytest.raises(ApiError) as error:
        await learning.save_answers(db_session, user.id, attempt.id, pick(article))
    assert error.value.code == "ATTEMPT_SUBMITTED"


async def test_one_active_attempt_enforced_by_database(db_session):
    user = await make_user(db_session)
    article = await make_article(db_session, await make_category(db_session))
    await learning.start_attempt(db_session, user.id, article.id)
    db_session.add(
        ReadingAttempt(user_id=user.id, article_id=article.id, attempt_number=2, answers={})
    )
    with pytest.raises(IntegrityError):
        await db_session.flush()


# --- XP -------------------------------------------------------------------------------------


async def test_first_pass_awards_question_points_once(db_session):
    user = await make_user(db_session)
    article = await make_article(db_session, await make_category(db_session))  # 2 + 3 points
    attempt = await learning.start_attempt(db_session, user.id, article.id)
    done = await learning.submit_attempt(db_session, user.id, attempt.id, pick(article))
    assert done.passed and done.xp_awarded == 5
    assert await xp(db_session, user) == 5
    progress = await learning.get_progress(db_session, user.id, article.id)
    assert (progress.status, progress.xp_awarded, progress.best_score_percent) == (
        "completed",
        5,
        100,
    )
    assert progress.attempts_count == 1 and progress.read_percent == 100


async def test_resubmitting_the_same_attempt_does_not_pay_again(db_session):
    user = await make_user(db_session)
    article = await make_article(db_session, await make_category(db_session))
    attempt = await learning.start_attempt(db_session, user.id, article.id)
    await learning.submit_attempt(db_session, user.id, attempt.id, pick(article))
    again = await learning.submit_attempt(
        db_session, user.id, attempt.id, pick(article, right=False)
    )
    assert again.score_percent == 100 and again.xp_awarded == 5  # unchanged by the resend
    assert await xp(db_session, user) == 5
    progress = await learning.get_progress(db_session, user.id, article.id)
    assert progress.attempts_count == 1


async def test_retries_after_pass_never_pay_and_best_score_is_kept(db_session):
    user = await make_user(db_session)
    article = await make_article(db_session, await make_category(db_session))
    first = await learning.start_attempt(db_session, user.id, article.id)
    await learning.submit_attempt(db_session, user.id, first.id, pick(article))
    retry = await learning.start_attempt(db_session, user.id, article.id)
    done = await learning.submit_attempt(db_session, user.id, retry.id, pick(article))
    assert done.passed and done.xp_awarded == 0
    worse = await learning.start_attempt(db_session, user.id, article.id)
    await learning.submit_attempt(db_session, user.id, worse.id, pick(article, right=False))
    assert await xp(db_session, user) == 5
    progress = await learning.get_progress(db_session, user.id, article.id)
    assert progress.best_score_percent == 100 and progress.attempts_count == 3
    assert progress.status == "completed"  # completion is sticky


async def test_failed_attempt_pays_nothing_then_later_pass_pays_once(db_session):
    user = await make_user(db_session)
    article = await make_article(db_session, await make_category(db_session))
    failed = await learning.start_attempt(db_session, user.id, article.id)
    done = await learning.submit_attempt(db_session, user.id, failed.id, pick(article, right=False))
    assert not done.passed and done.xp_awarded == 0 and await xp(db_session, user) == 0
    progress = await learning.get_progress(db_session, user.id, article.id)
    assert progress.status == "in_progress" and progress.best_score_percent == 0

    ok = await learning.start_attempt(db_session, user.id, article.id)
    await learning.submit_attempt(db_session, user.id, ok.id, pick(article))
    assert await xp(db_session, user) == 5


async def test_xp_is_per_article_and_per_user(db_session):
    a, b = await make_user(db_session, "a"), await make_user(db_session, "b")
    cat = await make_category(db_session)
    one, two = (
        await make_article(db_session, cat, "one"),
        await make_article(db_session, cat, "two"),
    )
    for user, article in ((a, one), (a, two), (b, one)):
        attempt = await learning.start_attempt(db_session, user.id, article.id)
        await learning.submit_attempt(db_session, user.id, attempt.id, pick(article))
    assert (await xp(db_session, a), await xp(db_session, b)) == (10, 5)


async def test_submit_updates_streak_activity_and_achievements(db_session):
    db_session.add(Achievement(code="hundred_xp", title="100 XP", metric="xp", threshold=100))
    await db_session.commit()
    user = await make_user(db_session)
    user.profile.xp = 95  # the 5 reading XP reach the 100 XP achievement
    await db_session.commit()
    article = await make_article(db_session, await make_category(db_session))
    attempt = await learning.start_attempt(db_session, user.id, article.id)
    await learning.submit_attempt(db_session, user.id, attempt.id, pick(article))
    assert await db_session.scalar(select(func.count()).select_from(LearningActivity)) == 1
    from app.db.models import UserAchievement

    assert await db_session.get(UserAchievement, (user.id, "hundred_xp")) is not None


async def test_submit_without_profile_row_does_not_crash(db_session):
    user = User(email="legacy@example.com", password_hash="x")
    db_session.add(user)
    await db_session.commit()
    article = await make_article(db_session, await make_category(db_session))
    attempt = await learning.start_attempt(db_session, user.id, article.id)
    done = await learning.submit_attempt(db_session, user.id, attempt.id, pick(article))
    assert done.passed


async def test_progress_listing(db_session):
    user = await make_user(db_session)
    cat = await make_category(db_session)
    one, two = (
        await make_article(db_session, cat, "one"),
        await make_article(db_session, cat, "two"),
    )
    await learning.update_read_progress(db_session, user.id, one.id, 20)
    attempt = await learning.start_attempt(db_session, user.id, two.id)
    await learning.submit_attempt(db_session, user.id, attempt.id, pick(two))
    assert len(await learning.list_progress(db_session, user.id)) == 2
    done = await learning.list_progress(db_session, user.id, status="completed")
    assert [p.article_id for p in done] == [two.id]
    assert await learning.list_progress(db_session, uuid.uuid4()) == []


# --- bookmarks ------------------------------------------------------------------------------


async def test_bookmarks_idempotent_and_listed(db_session):
    user, other = await make_user(db_session, "a"), await make_user(db_session, "b")
    cat = await make_category(db_session)
    one, two = (
        await make_article(db_session, cat, "one"),
        await make_article(db_session, cat, "two"),
    )
    first = await personal.add_bookmark(db_session, user.id, one.id)
    assert (await personal.add_bookmark(db_session, user.id, one.id)).id == first.id
    await personal.add_bookmark(db_session, user.id, two.id)
    await personal.add_bookmark(db_session, other.id, one.id)
    assert await db_session.scalar(select(func.count()).select_from(ReadingBookmark)) == 3
    assert {a.slug for a in await personal.list_bookmarks(db_session, user.id)} == {"one", "two"}
    assert await personal.is_bookmarked(db_session, user.id, one.id)

    assert await personal.remove_bookmark(db_session, user.id, one.id) is True
    assert await personal.remove_bookmark(db_session, user.id, one.id) is False
    assert not await personal.is_bookmarked(db_session, user.id, one.id)
    assert await personal.is_bookmarked(db_session, other.id, one.id)  # other user untouched


async def test_bookmarks_hide_unavailable_articles_but_can_be_removed(db_session):
    user = await make_user(db_session)
    article = await make_article(db_session, await make_category(db_session))
    await personal.add_bookmark(db_session, user.id, article.id)
    await content.set_status(db_session, article, "archived")
    assert await personal.list_bookmarks(db_session, user.id) == []
    assert await personal.remove_bookmark(db_session, user.id, article.id) is True
    with pytest.raises(ApiError):
        await personal.add_bookmark(db_session, user.id, article.id)


async def test_bookmarks_removed_with_article_or_user(db_session):
    user = await make_user(db_session)
    article = await make_article(db_session, await make_category(db_session))
    await personal.add_bookmark(db_session, user.id, article.id)
    await db_session.delete(await content.get_article(db_session, slug="a-trip"))
    await db_session.commit()
    assert await db_session.scalar(select(func.count()).select_from(ReadingBookmark)) == 0


# --- topic preferences ----------------------------------------------------------------------


async def test_topic_preferences_replace_and_are_per_user(db_session):
    user, other = await make_user(db_session, "a"), await make_user(db_session, "b")
    travel, food, sport = [await make_category(db_session, s) for s in ("travel", "food", "sport")]
    got = await personal.set_topic_preferences(db_session, user.id, [travel.id, food.id, food.id])
    assert {c.slug for c in got} == {"travel", "food"}
    await personal.set_topic_preferences(db_session, other.id, [sport.id])
    got = await personal.set_topic_preferences(db_session, user.id, [food.id, sport.id])
    assert {c.slug for c in got} == {"food", "sport"}
    assert {c.slug for c in await personal.get_topic_preferences(db_session, other.id)} == {"sport"}
    assert await personal.set_topic_preferences(db_session, user.id, []) == []
    assert await personal.set_topic_preferences(db_session, user.id, [food.id]) != []


async def test_topic_preferences_reject_unknown_and_inactive_without_changes(db_session):
    user = await make_user(db_session)
    travel = await make_category(db_session)
    off = await make_category(db_session, "off", is_active=False)
    await personal.set_topic_preferences(db_session, user.id, [travel.id])
    for bad in ([uuid.uuid4()], [travel.id, off.id]):
        with pytest.raises(ApiError) as error:
            await personal.set_topic_preferences(db_session, user.id, bad)
        assert error.value.status_code == 422
    assert [c.slug for c in await personal.get_topic_preferences(db_session, user.id)] == ["travel"]
    # Deactivating a category hides it from the learner's preferences without deleting them.
    await content.update_category(db_session, travel, is_active=False)
    assert await personal.get_topic_preferences(db_session, user.id) == []


async def test_published_quiz_is_locked_while_attempts_are_unfinished(db_session):
    user = await make_user(db_session)
    article = await make_article(db_session, await make_category(db_session))
    attempt = await learning.start_attempt(db_session, user.id, article.id)
    with pytest.raises(ApiError) as error:
        await content.replace_questions(db_session, article, [question("New")])
    assert (error.value.status_code, error.value.code) == (409, "QUIZ_LOCKED")
    assert len((await content.get_article(db_session, slug="a-trip")).questions) == 2

    await learning.submit_attempt(db_session, user.id, attempt.id, pick(article, right=False))
    updated = await content.replace_questions(db_session, article, [question("New")])
    assert [q.prompt for q in updated.questions] == ["New"]


async def test_draft_quiz_stays_editable_with_unfinished_attempts(db_session):
    user = await make_user(db_session)
    article = await make_article(db_session, await make_category(db_session))
    await learning.start_attempt(db_session, user.id, article.id)
    article = await content.set_status(db_session, article, "draft")
    updated = await content.replace_questions(db_session, article, [question("Draft edit")])
    assert [q.prompt for q in updated.questions] == ["Draft edit"]
