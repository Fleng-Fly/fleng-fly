"""Deduplicate explicitly identified tutor requests without a second history store."""

import sqlalchemy as sa
from alembic import op

revision = "20261101_1200"
down_revision = "20261018_1200"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("ai_usage", sa.Column("request_id", sa.Uuid(), nullable=True))
    op.create_index("ai_usage_request_key", "ai_usage", ["user_id", "request_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ai_usage_request_key", table_name="ai_usage")
    op.drop_column("ai_usage", "request_id")
