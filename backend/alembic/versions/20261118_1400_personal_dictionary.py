"""Personal dictionary: lesson-linked curated words and spaced-repetition-ready word state.

Additive only. Existing vocabulary rows keep their data; their course is backfilled from
their lesson and they are marked as manually added.
"""

import sqlalchemy as sa

from alembic import op

revision = "20261118_1400"
down_revision = "20261118_1200"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("course_vocabulary_items") as batch:
        batch.add_column(sa.Column("lesson_id", sa.Uuid(), nullable=True))
        batch.add_column(sa.Column("pronunciation", sa.String(120), nullable=True))
        batch.create_foreign_key(
            "fk_course_vocabulary_lesson", "lessons", ["lesson_id"], ["id"], ondelete="SET NULL"
        )
        batch.create_index("ix_course_vocabulary_items_lesson_id", ["lesson_id"])
    with op.batch_alter_table("vocabulary_items") as batch:
        batch.add_column(sa.Column("course_id", sa.Uuid(), nullable=True))
        batch.add_column(sa.Column("pronunciation", sa.String(120), nullable=True))
        batch.add_column(
            sa.Column("source", sa.String(10), server_default="manual", nullable=False)
        )
        batch.add_column(
            sa.Column("interval_days", sa.Integer(), server_default="0", nullable=False)
        )
        batch.add_column(sa.Column("repetitions", sa.Integer(), server_default="0", nullable=False))
        batch.add_column(sa.Column("last_reviewed_at", sa.DateTime(timezone=True), nullable=True))
        batch.create_foreign_key(
            "fk_vocabulary_items_course", "courses", ["course_id"], ["id"], ondelete="SET NULL"
        )
        batch.create_index("ix_vocabulary_items_course_id", ["course_id"])
        batch.create_index("ix_vocabulary_items_lesson_id", ["lesson_id"])
        batch.create_check_constraint("vocabulary_source_check", "source IN ('manual', 'lesson')")
    # Words a learner already saved from a lesson belong to that lesson's course.
    op.execute(
        "UPDATE vocabulary_items SET course_id = "
        "(SELECT lessons.course_id FROM lessons WHERE lessons.id = vocabulary_items.lesson_id) "
        "WHERE lesson_id IS NOT NULL"
    )


def downgrade() -> None:
    with op.batch_alter_table("vocabulary_items") as batch:
        batch.drop_constraint("vocabulary_source_check", type_="check")
        batch.drop_index("ix_vocabulary_items_lesson_id")
        batch.drop_index("ix_vocabulary_items_course_id")
        batch.drop_constraint("fk_vocabulary_items_course", type_="foreignkey")
        batch.drop_column("last_reviewed_at")
        batch.drop_column("repetitions")
        batch.drop_column("interval_days")
        batch.drop_column("source")
        batch.drop_column("pronunciation")
        batch.drop_column("course_id")
    with op.batch_alter_table("course_vocabulary_items") as batch:
        batch.drop_index("ix_course_vocabulary_items_lesson_id")
        batch.drop_constraint("fk_course_vocabulary_lesson", type_="foreignkey")
        batch.drop_column("pronunciation")
        batch.drop_column("lesson_id")
