"""Allow Fleng introductory A0 without deleting course dependants on SQLite."""

import sqlalchemy as sa

from alembic import op

revision = "20261110_1400"
down_revision = "20261110_1200"
branch_labels = None
depends_on = None

OLD = "level IN ('A1', 'A2', 'B1', 'B2', 'C1', 'C2')"
NEW = "level IN ('A0', 'A1', 'A2', 'B1', 'B2', 'C1', 'C2')"


def replace_check(expression: str) -> None:
    if op.get_bind().dialect.name == "sqlite":
        # Batch rebuild drops courses. Disable FK cascades OUTSIDE a transaction;
        # otherwise SQLite ignores the PRAGMA and could delete lessons/progress.
        with op.get_context().autocommit_block():
            connection = op.get_bind()
            enabled = connection.exec_driver_sql("PRAGMA foreign_keys").scalar()
            connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
            try:
                with op.batch_alter_table("courses", recreate="always") as batch:
                    batch.drop_constraint("courses_level_check", type_="check")
                    batch.create_check_constraint("courses_level_check", expression)
                if connection.exec_driver_sql("PRAGMA foreign_key_check").first() is not None:
                    raise RuntimeError("Foreign key violation after course constraint migration")
            finally:
                connection.exec_driver_sql(f"PRAGMA foreign_keys={int(bool(enabled))}")
    else:
        op.drop_constraint("courses_level_check", "courses", type_="check")
        op.create_check_constraint("courses_level_check", "courses", expression)


def upgrade() -> None:
    replace_check(NEW)


def downgrade() -> None:
    if not op.get_context().as_sql and op.get_bind().scalar(
        sa.text("SELECT count(*) FROM courses WHERE level = 'A0'")
    ):
        raise RuntimeError("Cannot remove A0 support while A0 courses exist")
    replace_check(OLD)
