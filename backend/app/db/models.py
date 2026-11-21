"""Database models.

Identity (`User`), learner profile (`Profile`), authentication sessions
(`RefreshToken`), learning progress (`Progress`), the learning catalog
(`Course`, `Lesson`) and exercises (`Exercise`, `ExerciseSubmission`,
`LessonProgress`).
"""

import uuid
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    false,
    func,
    true,
)
from sqlalchemy import text as sql_text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.levels import LearningLevel
from app.db.base import Base

EXERCISE_TYPES = ("single_choice", "text", "self_check")
LESSON_PROGRESS_STATUSES = ("in_progress", "completed")
READING_LEVELS = ("A0", "A1", "A2", "B1", "B2")
READING_ARTICLE_STATUSES = ("draft", "published", "archived")
READING_ATTEMPT_STATUSES = ("in_progress", "submitted")
READING_PROGRESS_STATUSES = ("in_progress", "completed")


class User(Base):
    """Credentials and identity. Passwords are stored as argon2id hashes."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    profile: Mapped["Profile | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    progress: Mapped["Progress | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class OAuthIdentity(Base):
    """A third-party identity (currently Google) linked to one user.

    `subject` is the provider's stable account id (`sub`), never the email: emails
    can change. One identity maps to one user, and a user has at most one identity
    per provider.
    """

    __tablename__ = "oauth_identities"
    __table_args__ = (
        UniqueConstraint("provider", "subject", name="oauth_identity_provider_subject_key"),
        UniqueConstraint("user_id", "provider", name="oauth_identity_user_provider_key"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Profile(Base):
    """Public-facing learner profile. One-to-one with User."""

    __tablename__ = "profiles"
    __table_args__ = (
        CheckConstraint(
            "daily_lessons_goal BETWEEN 1 AND 10", name="profiles_daily_lessons_goal_check"
        ),
        CheckConstraint(
            "daily_words_goal BETWEEN 1 AND 100", name="profiles_daily_words_goal_check"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    english_level: Mapped[str] = mapped_column(String(2), default="A1", server_default="A1")
    preferred_language: Mapped[str] = mapped_column(
        String(40), default="English", server_default="English"
    )
    level: Mapped[int] = mapped_column(Integer, default=1, server_default="1", nullable=False)
    xp: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    # Daily goals are settings only; the day's progress is derived from lesson_progress and
    # vocabulary_reviews. `timezone` is the learner's IANA zone (None = server policy).
    daily_lessons_goal: Mapped[int] = mapped_column(
        Integer, default=1, server_default="1", nullable=False
    )
    daily_words_goal: Mapped[int] = mapped_column(
        Integer, default=10, server_default="10", nullable=False
    )
    timezone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped[User] = relationship(back_populates="profile")


class Progress(Base):
    """Aggregate learning progress for one user. One-to-one with User.

    This holds per-user totals. When lessons exist, a separate per-lesson table
    (`LessonProgress`) will reference `lessons(id)`; keeping the aggregate here
    means that addition will not require migrating this table.
    """

    __tablename__ = "progress"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    lessons_started: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    lessons_completed: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    study_minutes: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    last_activity_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped[User] = relationship(back_populates="progress")


class RefreshToken(Base):
    """A single refresh-token session.

    The raw token is only ever sent to the client in an HttpOnly cookie. The
    database stores its SHA-256 hash, so a database leak does not reveal usable
    tokens. Rotation is tracked with `replaced_by_id`; presenting a revoked token
    is treated as reuse and revokes the whole user session set.
    """

    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    replaced_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("refresh_tokens.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped[User] = relationship(back_populates="refresh_tokens")


class Course(Base):
    """A learning track. `slug` is stable and globally unique.

    `level` accepts Fleng introductory A0 and CEFR A1–C2.
    Only `is_published` courses are exposed by the API.
    """

    __tablename__ = "courses"
    __table_args__ = (
        CheckConstraint(
            "level IN ('A0', 'A1', 'A2', 'B1', 'B2', 'C1', 'C2')",
            name="courses_level_check",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    level: Mapped[LearningLevel] = mapped_column(String(2), nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    is_published: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=false(), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    lessons: Mapped[list["Lesson"]] = relationship(
        back_populates="course",
        cascade="all, delete-orphan",
        order_by="Lesson.position",
    )


class Lesson(Base):
    """A lesson within a course.

    `theory` is plain text with a deliberately small, documented markup that the
    static frontend renders safely (never `innerHTML`): blocks are separated by
    blank lines; a block starting with `## ` is a heading; consecutive lines
    starting with `- ` are a list; anything else is a paragraph.

    `slug` is globally unique so `GET /lessons/{slug}` resolves without a course
    context. Only `is_published` lessons of `is_published` courses are exposed.
    """

    __tablename__ = "lessons"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    course_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), index=True, nullable=False
    )
    slug: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    summary: Mapped[str] = mapped_column(String, nullable=False)
    theory: Mapped[str] = mapped_column(Text, nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    estimated_minutes: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    is_published: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=false(), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    course: Mapped[Course] = relationship(back_populates="lessons")
    exercises: Mapped[list["Exercise"]] = relationship(
        back_populates="lesson",
        cascade="all, delete-orphan",
        order_by="Exercise.position",
    )


class Exercise(Base):
    """A question inside a lesson.

    Three types are supported (`EXERCISE_TYPES`):

    - `single_choice`: `options` is a list of `{id, text}` and
      `correct_option_id` holds the one correct option id.
    - `text`: `accepted_answers` is a list of accepted short answers (compared
      after normalisation: trimmed, collapsed whitespace, case-insensitive).
      Optional `letter_tiles` config supplies the word pattern and letter bank.
    - `self_check`: the learner answers in their own words and checks it
      themselves; the server records the attempt and never grades free text.
      `model_answer` is revealed only after submission.

    `correct_option_id`, `accepted_answers` and `model_answer` are grading
    secrets and must never appear in a public response before the learner
    submits.
    """

    __tablename__ = "exercises"
    __table_args__ = (
        CheckConstraint(
            "type IN ('single_choice', 'text', 'self_check')",
            name="exercises_type_check",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    lesson_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("lessons.id", ondelete="CASCADE"), index=True, nullable=False
    )
    slug: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    points: Mapped[int] = mapped_column(Integer, default=1, server_default="1", nullable=False)
    options: Mapped[list[dict[str, str]] | None] = mapped_column(JSON, nullable=True)
    letter_tiles: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    correct_option_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    accepted_answers: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    model_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    lesson: Mapped[Lesson] = relationship(back_populates="exercises")


class ExerciseSubmission(Base):
    """One learner's latest attempt at one exercise.

    Unique per `(user_id, exercise_id)`: retries update the row rather than
    inserting. `completed` is sticky (once true it never resets) and
    `xp_awarded` guarantees points are granted at most once per exercise.
    """

    __tablename__ = "exercise_submissions"
    __table_args__ = (
        UniqueConstraint("user_id", "exercise_id", name="exercise_submissions_user_exercise_key"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    exercise_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("exercises.id", ondelete="CASCADE"), index=True, nullable=False
    )
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    completed: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=false(), nullable=False
    )
    xp_awarded: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=false(), nullable=False
    )
    attempts: Mapped[int] = mapped_column(Integer, default=1, server_default="1", nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class LessonProgress(Base):
    """Per-learner state for one lesson.

    Unique per `(user_id, lesson_id)`. `status` moves from `in_progress` to
    `completed` once every published exercise in the lesson is completed; the
    transition happens at most once, so aggregate counters cannot double-count.
    """

    __tablename__ = "lesson_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "lesson_id", name="lesson_progress_user_lesson_key"),
        CheckConstraint(
            "status IN ('in_progress', 'completed')",
            name="lesson_progress_status_check",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    lesson_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("lessons.id", ondelete="CASCADE"), index=True, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), default="in_progress", server_default="in_progress", nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class VocabularyItem(Base):
    """One word in a learner's personal dictionary (shared by every course).

    Unique per `(user_id, word)`: a word learned in several lessons or courses is
    one entry that keeps the course/lesson it was first collected from. `source` is
    `lesson` for words collected automatically on lesson completion and `manual` for
    words the learner added. `interval_days`, `repetitions` and `last_reviewed_at`
    are the scheduling state a spaced-repetition policy needs; today's 1/7-day
    review policy fills them and a better scheduler can replace it without a new
    schema.
    """

    __tablename__ = "vocabulary_items"
    __table_args__ = (
        UniqueConstraint("user_id", "word", name="vocabulary_user_word_key"),
        CheckConstraint("source IN ('manual', 'lesson')", name="vocabulary_source_check"),
    )
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    lesson_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("lessons.id", ondelete="SET NULL"), index=True
    )
    course_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("courses.id", ondelete="SET NULL"), index=True
    )
    word: Mapped[str] = mapped_column(String(120))
    translation: Mapped[str] = mapped_column(String(300))
    example: Mapped[str] = mapped_column(String(1000), default="")
    pronunciation: Mapped[str | None] = mapped_column(String(120), nullable=True)
    source: Mapped[str] = mapped_column(
        String(10), default="manual", server_default="manual", nullable=False
    )
    learned: Mapped[bool] = mapped_column(Boolean, default=False)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    interval_days: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    repetitions: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    last_reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class VocabularyReview(Base):
    __tablename__ = "vocabulary_reviews"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("vocabulary_items.id", ondelete="CASCADE"), index=True
    )
    remembered: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LearningActivity(Base):
    __tablename__ = "learning_activity"
    __table_args__ = (UniqueConstraint("user_id", "day", name="activity_user_day_key"),)
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    day: Mapped[date] = mapped_column(Date)


class Achievement(Base):
    __tablename__ = "achievements"
    code: Mapped[str] = mapped_column(String(40), primary_key=True)
    title: Mapped[str] = mapped_column(String(100))
    metric: Mapped[str] = mapped_column(String(30))
    threshold: Mapped[int] = mapped_column(Integer)


class UserAchievement(Base):
    __tablename__ = "user_achievements"
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    achievement_code: Mapped[str] = mapped_column(ForeignKey("achievements.code"), primary_key=True)
    awarded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PasswordReset(Base):
    __tablename__ = "password_resets"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class EmailChange(Base):
    __tablename__ = "email_changes"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    new_email: Mapped[str] = mapped_column(String(320))
    authorization_hash: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class RequestLimit(Base):
    """Persistent fixed windows; unique keys and row locks coordinate workers."""

    __tablename__ = "request_limits"
    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    window: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    count: Mapped[int] = mapped_column(Integer, default=0)


class AIConversation(Base):
    __tablename__ = "ai_conversations"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    model: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AIMessage(Base):
    __tablename__ = "ai_messages"
    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant')", name="ai_message_role_check"),
    )
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ai_conversations.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    model: Mapped[str] = mapped_column(String(200))
    usage: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AIUsage(Base):
    __tablename__ = "ai_usage"
    __table_args__ = (Index("ai_usage_request_key", "user_id", "request_id", unique=True),)
    request_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    model: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(20), default="reserved")
    reserved_tokens: Mapped[int] = mapped_column(Integer)
    usage: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # UTC calendar day used for per-learner quotas and the global daily budget.
    day: Mapped[date] = mapped_column(Date, index=True, default=lambda: datetime.now(UTC).date())
    # Worst-case cost held before the provider call, in millionths of a USD.
    reserved_microusd: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    # Final charge; NULL while in flight, so the reservation counts until settled.
    cost_microusd: Mapped[int | None] = mapped_column(Integer)
    # provider | tariff | reserved | released
    cost_source: Mapped[str | None] = mapped_column(String(20))


class CourseVocabularyItem(Base):
    """Curated vocabulary: course words, each taught by one lesson (`lesson_id`).

    Completing that lesson copies the word into the learner's `VocabularyItem` list.
    The learning level is inherited from the course.
    """

    __tablename__ = "course_vocabulary_items"
    __table_args__ = (UniqueConstraint("course_id", "word", name="course_vocabulary_word_key"),)
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    course_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), index=True
    )
    # The lesson that teaches this word (NULL for course-level words without a lesson).
    lesson_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("lessons.id", ondelete="SET NULL"), index=True, nullable=True
    )
    word: Mapped[str] = mapped_column(String(120))
    translation: Mapped[str] = mapped_column(String(300))
    example: Mapped[str] = mapped_column(String(1000), default="", server_default="")
    pronunciation: Mapped[str | None] = mapped_column(String(120), nullable=True)


class FlashcardSession(Base):
    """Owned immutable card snapshot; source IDs survive deletion of original words."""

    __tablename__ = "vocabulary_flashcard_sessions"
    __table_args__ = (
        CheckConstraint("source IN ('my_words', 'course_words')", name="flashcard_source_check"),
        CheckConstraint(
            "status IN ('active', 'completed', 'empty')", name="flashcard_status_check"
        ),
    )
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    source: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20))
    cards: Mapped[list[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PlacementAttempt(Base):
    """Private, versioned diagnostic snapshot, independent of learning progress."""

    __tablename__ = "placement_attempts"
    __table_args__ = (
        CheckConstraint("status IN ('in_progress', 'completed')", name="placement_status_check"),
        Index("ix_placement_user_started", "user_id", "started_at"),
    )
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    bank_version: Mapped[str] = mapped_column(String(40), nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="in_progress", nullable=False)
    questions: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    answers: Mapped[dict[str, str]] = mapped_column(JSON, default=dict, nullable=False)
    result: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ReadingCategory(Base):
    """A topic that groups reading articles. `is_active=False` hides it and its articles."""

    __tablename__ = "reading_categories"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(String(500), default="", server_default="")
    position: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=true(), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    articles: Mapped[list["ReadingArticle"]] = relationship(back_populates="category")


class ReadingArticle(Base):
    """A reading text with an optional comprehension quiz.

    `level` is Fleng A0 (introductory) or CEFR A1-B2. A learner sees an article only when
    `status == 'published'` and its category is active; `published_at` is set on first
    publication. The category is `RESTRICT`ed so deleting a category never silently deletes
    articles (deactivate it instead).
    """

    __tablename__ = "reading_articles"
    __table_args__ = (
        CheckConstraint("level IN ('A0', 'A1', 'A2', 'B1', 'B2')", name="reading_article_level"),
        CheckConstraint(
            "status IN ('draft', 'published', 'archived')", name="reading_article_status"
        ),
        CheckConstraint("reading_minutes BETWEEN 1 AND 120", name="reading_article_minutes"),
        Index("ix_reading_articles_listing", "status", "level", "category_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    category_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("reading_categories.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    level: Mapped[str] = mapped_column(String(2), nullable=False)
    reading_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    cover_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    cover_alt: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(
        String(10), default="draft", server_default="draft", nullable=False
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    category: Mapped[ReadingCategory] = relationship(back_populates="articles")
    questions: Mapped[list["ReadingQuestion"]] = relationship(
        back_populates="article", cascade="all, delete-orphan", order_by="ReadingQuestion.position"
    )


class ReadingQuestion(Base):
    """A single-choice comprehension question about one article."""

    __tablename__ = "reading_questions"
    __table_args__ = (
        UniqueConstraint("article_id", "position", name="reading_question_position_key"),
        CheckConstraint("points BETWEEN 1 AND 10", name="reading_question_points"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    article_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("reading_articles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    points: Mapped[int] = mapped_column(Integer, default=1, server_default="1", nullable=False)

    article: Mapped[ReadingArticle] = relationship(back_populates="questions")
    answers: Mapped[list["ReadingAnswer"]] = relationship(
        back_populates="question", cascade="all, delete-orphan", order_by="ReadingAnswer.position"
    )


class ReadingAnswer(Base):
    """One answer option. The partial unique index allows at most one correct option."""

    __tablename__ = "reading_answers"
    __table_args__ = (
        UniqueConstraint("question_id", "position", name="reading_answer_position_key"),
        Index(
            "reading_answer_one_correct",
            "question_id",
            unique=True,
            sqlite_where=sql_text("is_correct"),
            postgresql_where=sql_text("is_correct"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    question_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("reading_questions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(String(500), nullable=False)
    is_correct: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=false(), nullable=False
    )

    question: Mapped[ReadingQuestion] = relationship(back_populates="answers")


class ReadingAttempt(Base):
    """One pass through an article's quiz.

    `answers` maps question id -> answer id and is saved while `in_progress` (so a learner
    can resume). Submitting freezes the graded `result` snapshot, so later edits of the
    article never change history. At most one attempt per learner and article is in
    progress; `attempt_number` is sequential per learner and article.
    """

    __tablename__ = "reading_attempts"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "article_id", "attempt_number", name="reading_attempt_number_key"
        ),
        CheckConstraint("status IN ('in_progress', 'submitted')", name="reading_attempt_status"),
        Index(
            "reading_attempt_one_active",
            "user_id",
            "article_id",
            unique=True,
            sqlite_where=sql_text("status = 'in_progress'"),
            postgresql_where=sql_text("status = 'in_progress'"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    article_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("reading_articles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(12), default="in_progress", server_default="in_progress", nullable=False
    )
    answers: Mapped[dict[str, str]] = mapped_column(JSON, default=dict, nullable=False)
    result: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    points_earned: Mapped[int | None] = mapped_column(Integer, nullable=True)
    points_possible: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score_percent: Mapped[int | None] = mapped_column(Integer, nullable=True)
    passed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    xp_awarded: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ReadingUserProgress(Base):
    """Per-learner state for one article. Unique per `(user_id, article_id)`.

    `read_percent` only grows. `completed` happens once: on a passing quiz attempt, or on
    reaching 100% for an article without questions. `xp_awarded` is the XP granted for this
    article; it is claimed with a conditional UPDATE so it is paid at most once.
    """

    __tablename__ = "reading_user_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "article_id", name="reading_progress_user_article_key"),
        CheckConstraint("read_percent BETWEEN 0 AND 100", name="reading_progress_percent"),
        CheckConstraint("status IN ('in_progress', 'completed')", name="reading_progress_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    article_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("reading_articles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(12), default="in_progress", server_default="in_progress", nullable=False
    )
    read_percent: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    best_score_percent: Mapped[int | None] = mapped_column(Integer, nullable=True)
    attempts_count: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    xp_awarded: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_read_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ReadingBookmark(Base):
    """A learner's saved article. Unique per `(user_id, article_id)`."""

    __tablename__ = "reading_bookmarks"
    __table_args__ = (
        UniqueConstraint("user_id", "article_id", name="reading_bookmark_user_article_key"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    article_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("reading_articles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ReadingTopicPreference(Base):
    """A category a learner wants to read about. Unique per `(user_id, category_id)`."""

    __tablename__ = "reading_topic_preferences"
    __table_args__ = (
        UniqueConstraint("user_id", "category_id", name="reading_topic_user_category_key"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("reading_categories.id", ondelete="CASCADE"), index=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
