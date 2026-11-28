"""Upgrade a newly created temporary SQLite database; never use a configured database."""

from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
import tempfile
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    for path in (ROOT / ".env", ROOT / "backend/.env"):
        if path.exists():
            raise SystemExit(
                "Migration smoke requires a clean worktree without .env files."
            )
    # Do not forward application credentials or hosted-storage flags.
    allowed = {
        "PATH",
        "HOME",
        "USERPROFILE",
        "SYSTEMROOT",
        "WINDIR",
        "TEMP",
        "TMP",
        "TMPDIR",
    }
    env = {key: value for key, value in os.environ.items() if key.upper() in allowed}
    with tempfile.TemporaryDirectory(prefix="fleng-migration-smoke-") as directory:
        database = Path(directory) / "migration.sqlite3"
        env.update(
            APP_ENV="development",
            DATABASE_URL="sqlite+aiosqlite:///" + database.as_posix(),
            AI_ENABLED="false",
            OPENROUTER_API_KEY="",
            RESET_DELIVERY="disabled",
            JWT_ACCESS_SECRET="disposable-migration-smoke-secret-0123456789",
        )
        from alembic.config import Config
        from alembic.script import ScriptDirectory

        config = Config(str(ROOT / "backend/alembic.ini"))
        config.set_main_option("script_location", str(ROOT / "backend/alembic"))
        heads = ScriptDirectory.from_config(config).get_heads()
        if len(heads) != 1:
            raise SystemExit(f"Expected one Alembic head, found {heads}")
        for arguments in (
            ("heads",),
            ("upgrade", "head"),
            ("upgrade", "head"),
            ("check",),
        ):
            print("Alembic " + " ".join(arguments), flush=True)
            subprocess.run(
                [sys.executable, "-m", "alembic", *arguments],
                cwd=ROOT / "backend",
                env=env,
                check=True,
                timeout=120,
            )
        with closing(sqlite3.connect(database)) as connection:
            revisions = [
                row[0]
                for row in connection.execute("SELECT version_num FROM alembic_version")
            ]
            if revisions != heads:
                raise SystemExit(
                    f"Applied revisions {revisions} do not match heads {heads}"
                )
            if connection.execute("PRAGMA integrity_check").fetchone() != ("ok",):
                raise SystemExit("SQLite integrity check failed")
            if connection.execute("PRAGMA foreign_key_check").fetchall():
                raise SystemExit("SQLite foreign key check failed")
        print(
            f"Migration smoke passed: one head {heads[0]}, repeat upgrade, ORM drift and integrity."
        )


if __name__ == "__main__":
    main()
