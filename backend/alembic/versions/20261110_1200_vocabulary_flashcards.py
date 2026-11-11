"""Shared course vocabulary and persistent owned flashcard snapshots."""

import sqlalchemy as sa

from alembic import op

revision = "20261110_1200"
down_revision = "20261101_1200"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "course_vocabulary_items",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "course_id", sa.Uuid(), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("word", sa.String(120), nullable=False),
        sa.Column("translation", sa.String(300), nullable=False),
        sa.Column("example", sa.String(1000), server_default="", nullable=False),
        sa.UniqueConstraint("course_id", "word", name="course_vocabulary_word_key"),
    )
    op.create_index(
        "ix_course_vocabulary_items_course_id", "course_vocabulary_items", ["course_id"]
    )
    op.create_table(
        "vocabulary_flashcard_sessions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("cards", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("source IN ('my_words', 'course_words')", name="flashcard_source_check"),
        sa.CheckConstraint(
            "status IN ('active', 'completed', 'empty')", name="flashcard_status_check"
        ),
    )
    op.create_index(
        "ix_vocabulary_flashcard_sessions_user_id", "vocabulary_flashcard_sessions", ["user_id"]
    )


def downgrade() -> None:
    op.drop_table("vocabulary_flashcard_sessions")
    op.drop_table("course_vocabulary_items")
