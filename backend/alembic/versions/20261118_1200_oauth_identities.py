"""Linked third-party (Google) identities. Additive: no existing table is changed."""

import sqlalchemy as sa

from alembic import op

revision = "20261118_1200"
down_revision = "20261117_1200"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "oauth_identities",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("provider", sa.String(20), nullable=False),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("provider", "subject", name="oauth_identity_provider_subject_key"),
        sa.UniqueConstraint("user_id", "provider", name="oauth_identity_user_provider_key"),
    )


def downgrade() -> None:
    op.drop_table("oauth_identities")
