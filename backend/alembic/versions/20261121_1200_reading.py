"""Reading module: categories, articles, quiz questions/answers, attempts, progress,
bookmarks and topic preferences.

Additive only: eight new tables, no existing table or row is touched. Downgrade drops
exactly these tables (reading data only).
"""

import sqlalchemy as sa

from alembic import op

revision = "20261121_1200"
down_revision = "20261120_1200"
branch_labels = None
depends_on = None


def _id() -> sa.Column:
    return sa.Column("id", sa.Uuid(), primary_key=True)


def _fk(name: str, target: str, *, ondelete: str = "CASCADE") -> sa.Column:
    return sa.Column(name, sa.Uuid(), sa.ForeignKey(target, ondelete=ondelete), nullable=False)


def _now(name: str) -> sa.Column:
    return sa.Column(name, sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)


def upgrade() -> None:
    op.create_table(
        "reading_categories",
        _id(),
        sa.Column("slug", sa.String(80), nullable=False, unique=True),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column("description", sa.String(500), server_default="", nullable=False),
        sa.Column("position", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        _now("created_at"),
        _now("updated_at"),
    )
    op.create_table(
        "reading_articles",
        _id(),
        _fk("category_id", "reading_categories.id", ondelete="RESTRICT"),
        sa.Column("slug", sa.String(120), nullable=False, unique=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("level", sa.String(2), nullable=False),
        sa.Column("reading_minutes", sa.Integer(), nullable=False),
        sa.Column("cover_image_url", sa.String(500), nullable=True),
        sa.Column("cover_alt", sa.String(200), nullable=True),
        sa.Column("status", sa.String(10), server_default="draft", nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        _now("created_at"),
        _now("updated_at"),
        sa.CheckConstraint("level IN ('A0', 'A1', 'A2', 'B1', 'B2')", name="reading_article_level"),
        sa.CheckConstraint(
            "status IN ('draft', 'published', 'archived')", name="reading_article_status"
        ),
        sa.CheckConstraint("reading_minutes BETWEEN 1 AND 120", name="reading_article_minutes"),
    )
    op.create_index("ix_reading_articles_category_id", "reading_articles", ["category_id"])
    op.create_index(
        "ix_reading_articles_listing", "reading_articles", ["status", "level", "category_id"]
    )
    op.create_table(
        "reading_questions",
        _id(),
        _fk("article_id", "reading_articles.id"),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("points", sa.Integer(), server_default="1", nullable=False),
        sa.UniqueConstraint("article_id", "position", name="reading_question_position_key"),
        sa.CheckConstraint("points BETWEEN 1 AND 10", name="reading_question_points"),
    )
    op.create_index("ix_reading_questions_article_id", "reading_questions", ["article_id"])
    op.create_table(
        "reading_answers",
        _id(),
        _fk("question_id", "reading_questions.id"),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("text", sa.String(500), nullable=False),
        sa.Column("is_correct", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.UniqueConstraint("question_id", "position", name="reading_answer_position_key"),
    )
    op.create_index("ix_reading_answers_question_id", "reading_answers", ["question_id"])
    op.create_index(
        "reading_answer_one_correct",
        "reading_answers",
        ["question_id"],
        unique=True,
        sqlite_where=sa.text("is_correct"),
        postgresql_where=sa.text("is_correct"),
    )
    op.create_table(
        "reading_attempts",
        _id(),
        _fk("user_id", "users.id"),
        _fk("article_id", "reading_articles.id"),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(12), server_default="in_progress", nullable=False),
        sa.Column("answers", sa.JSON(), nullable=False),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("points_earned", sa.Integer(), nullable=True),
        sa.Column("points_possible", sa.Integer(), nullable=True),
        sa.Column("score_percent", sa.Integer(), nullable=True),
        sa.Column("passed", sa.Boolean(), nullable=True),
        sa.Column("xp_awarded", sa.Integer(), server_default="0", nullable=False),
        _now("started_at"),
        _now("updated_at"),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "user_id", "article_id", "attempt_number", name="reading_attempt_number_key"
        ),
        sa.CheckConstraint("status IN ('in_progress', 'submitted')", name="reading_attempt_status"),
    )
    op.create_index("ix_reading_attempts_user_id", "reading_attempts", ["user_id"])
    op.create_index("ix_reading_attempts_article_id", "reading_attempts", ["article_id"])
    op.create_index(
        "reading_attempt_one_active",
        "reading_attempts",
        ["user_id", "article_id"],
        unique=True,
        sqlite_where=sa.text("status = 'in_progress'"),
        postgresql_where=sa.text("status = 'in_progress'"),
    )
    op.create_table(
        "reading_user_progress",
        _id(),
        _fk("user_id", "users.id"),
        _fk("article_id", "reading_articles.id"),
        sa.Column("status", sa.String(12), server_default="in_progress", nullable=False),
        sa.Column("read_percent", sa.Integer(), server_default="0", nullable=False),
        sa.Column("best_score_percent", sa.Integer(), nullable=True),
        sa.Column("attempts_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("xp_awarded", sa.Integer(), server_default="0", nullable=False),
        _now("started_at"),
        _now("last_read_at"),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("user_id", "article_id", name="reading_progress_user_article_key"),
        sa.CheckConstraint("read_percent BETWEEN 0 AND 100", name="reading_progress_percent"),
        sa.CheckConstraint(
            "status IN ('in_progress', 'completed')", name="reading_progress_status"
        ),
    )
    op.create_index("ix_reading_user_progress_user_id", "reading_user_progress", ["user_id"])
    op.create_index("ix_reading_user_progress_article_id", "reading_user_progress", ["article_id"])
    op.create_table(
        "reading_bookmarks",
        _id(),
        _fk("user_id", "users.id"),
        _fk("article_id", "reading_articles.id"),
        _now("created_at"),
        sa.UniqueConstraint("user_id", "article_id", name="reading_bookmark_user_article_key"),
    )
    op.create_index("ix_reading_bookmarks_user_id", "reading_bookmarks", ["user_id"])
    op.create_index("ix_reading_bookmarks_article_id", "reading_bookmarks", ["article_id"])
    op.create_table(
        "reading_topic_preferences",
        _id(),
        _fk("user_id", "users.id"),
        _fk("category_id", "reading_categories.id"),
        _now("created_at"),
        sa.UniqueConstraint("user_id", "category_id", name="reading_topic_user_category_key"),
    )
    op.create_index(
        "ix_reading_topic_preferences_user_id", "reading_topic_preferences", ["user_id"]
    )
    op.create_index(
        "ix_reading_topic_preferences_category_id", "reading_topic_preferences", ["category_id"]
    )


def downgrade() -> None:
    # Children before parents; only Reading tables are dropped.
    for table in (
        "reading_topic_preferences",
        "reading_bookmarks",
        "reading_user_progress",
        "reading_attempts",
        "reading_answers",
        "reading_questions",
        "reading_articles",
        "reading_categories",
    ):
        op.drop_table(table)
