"""Add dictionary metadata (transcription, part of speech, topic) to vocabulary."""

import sqlalchemy as sa

from alembic import op

revision = "20261116_1200"
down_revision = "20261114_1200"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "vocabulary_items",
        sa.Column("transcription", sa.String(120), server_default="", nullable=False),
    )
    op.add_column(
        "vocabulary_items",
        sa.Column("part_of_speech", sa.String(40), server_default="", nullable=False),
    )
    op.add_column(
        "vocabulary_items",
        sa.Column("topic", sa.String(80), server_default="", nullable=False),
    )
    op.add_column(
        "course_vocabulary_items",
        sa.Column("transcription", sa.String(120), server_default="", nullable=False),
    )
    op.add_column(
        "course_vocabulary_items",
        sa.Column("part_of_speech", sa.String(40), server_default="", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("course_vocabulary_items", "part_of_speech")
    op.drop_column("course_vocabulary_items", "transcription")
    op.drop_column("vocabulary_items", "topic")
    op.drop_column("vocabulary_items", "part_of_speech")
    op.drop_column("vocabulary_items", "transcription")
