"""One-use password-authorized email changes."""

import sqlalchemy as sa
from alembic import op

revision = "20261116_1400"
down_revision = "20261116_1200"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "email_changes",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("new_email", sa.String(320), nullable=False),
        sa.Column("authorization_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_email_changes_user_id", "email_changes", ["user_id"])


def downgrade() -> None:
    op.drop_table("email_changes")
