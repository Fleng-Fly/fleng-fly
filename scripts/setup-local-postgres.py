"""Interactive native PostgreSQL setup. Run with backend/.venv/bin/python.

Uses existing postgres administration via sudo and psql. Passwords are entered
only in the invoking terminal, never command arguments or printed output.
No PostgreSQL system configuration or unrelated roles/databases are modified.
"""

import asyncio
import getpass
import os
import re
import secrets
import subprocess
from pathlib import Path

import asyncpg
from dotenv import dotenv_values
from sqlalchemy.engine import URL, make_url

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"


async def configure() -> None:
    if os.environ.get("DATABASE_URL"):
        raise RuntimeError("DATABASE_URL is exported; unset it or review it before running setup")
    existing = dotenv_values(ENV_PATH) if ENV_PATH.exists() else {}
    if existing.get("DATABASE_URL"):
        url = make_url(existing["DATABASE_URL"])
        if (
            url.username != "fleng"
            or url.database != "fleng_db"
            or url.host not in {"localhost", "127.0.0.1"}
        ):
            raise RuntimeError(
                "Existing DATABASE_URL targets another database; manual review required"
            )
        print("An existing local fleng_db URL will be updated after password verification.")
    subprocess.run(
        [
            "sudo",
            "-u",
            "postgres",
            "psql",
            "-X",
            "-d",
            "postgres",
            "-f",
            str(ROOT / "scripts/setup-local-postgres.sql"),
        ],
        check=True,
    )
    password = getpass.getpass("Re-enter the fleng database password to verify and save locally: ")
    if not password:
        raise RuntimeError("An empty database password is not allowed")
    connection = await asyncpg.connect(
        host="127.0.0.1", port=5432, user="fleng", password=password, database="fleng_db", timeout=5
    )
    try:
        assert await connection.fetchval("SELECT current_user") == "fleng"
        assert await connection.fetchval("SELECT current_database()") == "fleng_db"
    finally:
        await connection.close()
    # A successful login alone does not prove that pg_hba enforces passwords.
    try:
        unexpected = await asyncpg.connect(
            host="127.0.0.1",
            port=5432,
            user="fleng",
            password=secrets.token_urlsafe(48),
            database="fleng_db",
            timeout=5,
        )
    except asyncpg.InvalidPasswordError:
        pass
    else:
        await unexpected.close()
        print("TCP accepted an incorrect password. Authentication-rule review is required.")
        print("No PostgreSQL configuration was changed; ask the agent to review this result.")
        raise RuntimeError("Password authentication is not enforced")
    url = URL.create(
        "postgresql+asyncpg",
        username="fleng",
        password=password,
        host="127.0.0.1",
        port=5432,
        database="fleng_db",
    ).render_as_string(hide_password=False)
    content = ENV_PATH.read_text() if ENV_PATH.exists() else ""
    line = "DATABASE_URL=" + url
    if re.search(r"^\s*(?:export\s+)?DATABASE_URL\s*=", content, re.MULTILINE):
        content = re.sub(
            r"^\s*(?:export\s+)?DATABASE_URL\s*=.*$", lambda _: line, content, flags=re.MULTILINE
        )
    else:
        content = content.rstrip("\n") + ("\n" if content else "") + line + "\n"
    descriptor = os.open(ENV_PATH, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w") as env_file:
        os.fchmod(env_file.fileno(), 0o600)
        env_file.write(content)
    print("Verified fleng -> fleng_db over TCP; saved DATABASE_URL in ignored .env (mode 0600).")
    print("No password has been printed. No system-wide PostgreSQL configuration was changed.")


if __name__ == "__main__":
    try:
        asyncio.run(configure())
    except (Exception, KeyboardInterrupt) as exc:
        # Exception strings can contain connection details; print only the type.
        print(f"Setup stopped ({type(exc).__name__}). Existing database data was preserved.")
        raise SystemExit(1) from None
