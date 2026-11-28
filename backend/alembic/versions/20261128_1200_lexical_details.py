"""Store sourced lexical details on course words."""

import sqlalchemy as sa

from alembic import op

revision = "20261128_1200"
down_revision = "20261124_1200"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("course_vocabulary_items", sa.Column("lexical_details", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("course_vocabulary_items", "lexical_details")
