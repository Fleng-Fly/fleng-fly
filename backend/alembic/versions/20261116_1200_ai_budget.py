"""Persist UTC-day AI quotas and the global provider budget in ai_usage."""

import sqlalchemy as sa
from alembic import op

revision = "20261116_1200"
down_revision = "20261114_1200"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("ai_usage", sa.Column("day", sa.Date(), nullable=True))
    op.add_column(
        "ai_usage",
        sa.Column("reserved_microusd", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column("ai_usage", sa.Column("cost_microusd", sa.Integer(), nullable=True))
    op.add_column("ai_usage", sa.Column("cost_source", sa.String(length=20), nullable=True))
    # Existing rows keep counting toward today's per-learner quota after deploy.
    if op.get_context().dialect.name == "postgresql":
        op.execute("UPDATE ai_usage SET day = (created_at AT TIME ZONE 'UTC')::date")
    else:
        op.execute("UPDATE ai_usage SET day = date(created_at)")
    with op.batch_alter_table("ai_usage") as batch:
        batch.alter_column("day", existing_type=sa.Date(), nullable=False)
    op.create_index("ix_ai_usage_day", "ai_usage", ["day"])


def downgrade() -> None:
    op.drop_index("ix_ai_usage_day", table_name="ai_usage")
    with op.batch_alter_table("ai_usage") as batch:
        batch.drop_column("cost_source")
        batch.drop_column("cost_microusd")
        batch.drop_column("reserved_microusd")
        batch.drop_column("day")
