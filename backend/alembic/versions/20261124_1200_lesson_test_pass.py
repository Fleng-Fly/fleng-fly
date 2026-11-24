"""Persist the first pass independently of course mastery."""

import sqlalchemy as sa

from alembic import op

revision = "20261124_1200"
down_revision = "20261122_1200"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("exercise_submissions", sa.Column("first_result", sa.JSON(), nullable=True))
    op.add_column(
        "lesson_progress", sa.Column("test_finished_at", sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("lesson_progress", "test_finished_at")
    op.drop_column("exercise_submissions", "first_result")
