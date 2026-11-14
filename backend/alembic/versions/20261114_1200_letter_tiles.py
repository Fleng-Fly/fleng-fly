"""Add optional letter-tile configuration to short-answer exercises."""

import sqlalchemy as sa
from alembic import op
from alembic.script import ScriptDirectory

revision = "20261114_1200"
down_revision = "20261110_1400"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if op.get_context().as_sql:
        op.add_column("exercises", sa.Column("letter_tiles", sa.JSON(), nullable=True))
        return
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("exercises")}
    if "letter_tiles" in columns:
        # The distributed desktop fork used the vocabulary revision ID for tiles.
        # Bring that exact legacy schema forward without restamping or losing rows.
        tables = set(inspector.get_table_names())
        vocabulary = {"course_vocabulary_items", "vocabulary_flashcard_sessions"}
        if not tables & vocabulary:
            scripts = ScriptDirectory.from_config(op.get_context().config)
            scripts.get_revision("20261110_1200").module.upgrade()
        elif tables & vocabulary != vocabulary:
            raise RuntimeError("Incomplete vocabulary schema; restore a verified backup")
    else:
        op.add_column("exercises", sa.Column("letter_tiles", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("exercises", "letter_tiles")
