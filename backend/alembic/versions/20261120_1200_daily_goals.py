"""Daily goals: per-learner goal settings and time zone on profiles.

Additive. Existing profiles get the defaults (1 lesson, 10 words) and no time zone,
which keeps using the server learning policy. Progress is derived, never stored.
"""

import sqlalchemy as sa

from alembic import op

revision = "20261120_1200"
down_revision = "20261118_1400"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("profiles") as batch:
        batch.add_column(
            sa.Column("daily_lessons_goal", sa.Integer(), server_default="1", nullable=False)
        )
        batch.add_column(
            sa.Column("daily_words_goal", sa.Integer(), server_default="10", nullable=False)
        )
        batch.add_column(sa.Column("timezone", sa.String(64), nullable=True))
        batch.create_check_constraint(
            "profiles_daily_lessons_goal_check", "daily_lessons_goal BETWEEN 1 AND 10"
        )
        batch.create_check_constraint(
            "profiles_daily_words_goal_check", "daily_words_goal BETWEEN 1 AND 100"
        )


def downgrade() -> None:
    with op.batch_alter_table("profiles") as batch:
        batch.drop_constraint("profiles_daily_words_goal_check", type_="check")
        batch.drop_constraint("profiles_daily_lessons_goal_check", type_="check")
        batch.drop_column("timezone")
        batch.drop_column("daily_words_goal")
        batch.drop_column("daily_lessons_goal")
