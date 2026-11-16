"""Learning support, password reset and AI persistence.

Revision ID: 20261018_1200
Revises: 20261011_1400
"""

import sqlalchemy as sa
from alembic import op

revision = "20261018_1200"
down_revision = "20261011_1400"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "profiles",
        sa.Column("english_level", sa.String(length=2), server_default="A1", nullable=False),
    )
    op.add_column(
        "profiles",
        sa.Column(
            "preferred_language", sa.String(length=40), server_default="English", nullable=False
        ),
    )
    op.create_table(
        "achievements",
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("metric", sa.String(length=30), nullable=False),
        sa.Column("threshold", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("code"),
    )
    op.create_table(
        "request_limits",
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("window", sa.DateTime(timezone=True), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("key", "window"),
    )
    op.create_table(
        "ai_conversations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("model", sa.String(length=200), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "ai_usage",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("model", sa.String(length=200), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("reserved_tokens", sa.Integer(), nullable=False),
        sa.Column("usage", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "learning_activity",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "day", name="activity_user_day_key"),
    )
    op.create_table(
        "password_resets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_table(
        "user_achievements",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("achievement_code", sa.String(length=40), nullable=False),
        sa.Column(
            "awarded_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["achievement_code"],
            ["achievements.code"],
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "achievement_code"),
    )
    op.create_table(
        "ai_messages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("model", sa.String(length=200), nullable=False),
        sa.Column("usage", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("role IN ('user', 'assistant')", name="ai_message_role_check"),
        sa.ForeignKeyConstraint(["conversation_id"], ["ai_conversations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "vocabulary_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("lesson_id", sa.Uuid(), nullable=True),
        sa.Column("word", sa.String(length=120), nullable=False),
        sa.Column("translation", sa.String(length=300), nullable=False),
        sa.Column("example", sa.String(length=1000), nullable=False),
        sa.Column("learned", sa.Boolean(), nullable=False),
        sa.Column(
            "due_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["lesson_id"], ["lessons.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "word", name="vocabulary_user_word_key"),
    )
    op.create_table(
        "vocabulary_reviews",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("item_id", sa.Uuid(), nullable=False),
        sa.Column("remembered", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["item_id"], ["vocabulary_items.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ai_conversations_user_id", "ai_conversations", ["user_id"])
    op.create_index("ix_ai_usage_user_id", "ai_usage", ["user_id"])
    op.create_index("ix_learning_activity_user_id", "learning_activity", ["user_id"])
    op.create_index("ix_password_resets_user_id", "password_resets", ["user_id"])
    op.create_index("ix_ai_messages_conversation_id", "ai_messages", ["conversation_id"])
    op.create_index("ix_vocabulary_items_user_id", "vocabulary_items", ["user_id"])
    op.create_index("ix_vocabulary_reviews_item_id", "vocabulary_reviews", ["item_id"])
    op.bulk_insert(
        sa.table(
            "achievements",
            sa.column("code", sa.String),
            sa.column("title", sa.String),
            sa.column("metric", sa.String),
            sa.column("threshold", sa.Integer),
        ),
        [
            {"code": "first_lesson", "title": "First Lesson", "metric": "lessons", "threshold": 1},
            {
                "code": "seven_day_streak",
                "title": "7-Day Streak",
                "metric": "streak",
                "threshold": 7,
            },
            {"code": "hundred_xp", "title": "100 XP", "metric": "xp", "threshold": 100},
            {
                "code": "ten_lessons",
                "title": "10 Lessons Completed",
                "metric": "lessons",
                "threshold": 10,
            },
            {
                "code": "vocabulary_beginner",
                "title": "Vocabulary Beginner",
                "metric": "vocabulary",
                "threshold": 5,
            },
        ],
    )


def downgrade() -> None:
    op.drop_table("vocabulary_reviews")
    op.drop_table("vocabulary_items")
    op.drop_table("ai_messages")
    op.drop_table("user_achievements")
    op.drop_table("password_resets")
    op.drop_table("learning_activity")
    op.drop_table("ai_usage")
    op.drop_table("ai_conversations")
    op.drop_table("request_limits")
    op.drop_table("achievements")
    op.drop_column("profiles", "preferred_language")
    op.drop_column("profiles", "english_level")
