"""Independent placement attempts; no profile, XP or progress changes."""

import sqlalchemy as sa

from alembic import op

revision = "20261117_1200"
down_revision = "20261116_1400"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "placement_attempts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("bank_version", sa.String(40), nullable=False),
        sa.Column("scoring_version", sa.String(40), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("questions", sa.JSON(), nullable=False),
        sa.Column("answers", sa.JSON(), nullable=False),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column(
            "started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('in_progress', 'completed')", name="placement_status_check"),
    )
    op.create_index("ix_placement_user_started", "placement_attempts", ["user_id", "started_at"])


def downgrade() -> None:
    op.drop_table("placement_attempts")
