"""Reading study time: per-learner total + crediting cursor, and per-article daily seconds.

Additive only: two new tables, no existing table or row is touched. Downgrade drops exactly
these tables (measured reading time only).
"""

import sqlalchemy as sa

from alembic import op

revision = "20261122_1200"
down_revision = "20261121_1200"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "reading_study_totals",
        sa.Column(
            "user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
        ),
        sa.Column("total_seconds", sa.Integer(), server_default="0", nullable=False),
        sa.Column("credited_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("total_seconds >= 0", name="reading_study_total_seconds"),
    )
    op.create_table(
        "reading_study_days",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "article_id",
            sa.Uuid(),
            sa.ForeignKey("reading_articles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("seconds", sa.Integer(), server_default="0", nullable=False),
        sa.UniqueConstraint("user_id", "article_id", "day", name="reading_study_day_key"),
        sa.CheckConstraint("seconds >= 0", name="reading_study_day_seconds"),
    )
    op.create_index("ix_reading_study_days_article_id", "reading_study_days", ["article_id"])
    op.create_index("ix_reading_study_days_user_day", "reading_study_days", ["user_id", "day"])


def downgrade() -> None:
    op.drop_table("reading_study_days")
    op.drop_table("reading_study_totals")
