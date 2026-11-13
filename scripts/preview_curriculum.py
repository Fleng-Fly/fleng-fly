"""Prepare/start an isolated, authenticated local curriculum preview.

No default application database, user data or production connection is used.
Each prepare creates a new private directory and refuses an existing directory.
"""

import argparse
import asyncio
import json
import os
import secrets
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
DEFAULT_DIRECTORY = Path("/tmp") / f"fleng-curriculum-preview-{os.getuid()}"
sys.path.insert(0, str(BACKEND))


def configure(directory: Path, marker: dict, port: int) -> None:
    # Explicit overrides isolate DB, JWTs, refresh cookies and all optional external calls.
    os.environ.update(
        APP_ENV="development",
        DATABASE_URL="sqlite+aiosqlite:///"
        + str(directory / "curriculum-preview.sqlite3"),
        JWT_ACCESS_SECRET=marker["jwt_secret"],
        REFRESH_COOKIE_NAME="fleng_curriculum_preview",
        COOKIE_SECURE="false",
        COOKIE_SAMESITE="lax",
        PORT=str(port),
        CORS_ORIGIN=f"http://127.0.0.1:{port}",
        RENDER_EXTERNAL_URL="",
        FRONTEND_DIR=str(ROOT / "frontend"),
        AI_ENABLED="false",
        OPENROUTER_API_KEY="",
        RESET_DELIVERY="disabled",
        TRUSTED_PROXY_IPS="",
    )


async def populate(marker: dict) -> dict:
    from app.db.curriculum import content_sha, import_curriculum, load_curriculum
    from app.db.seed import seed_catalog
    from app.db.session import SessionLocal, engine
    from app.modules.auth.service import register_user

    try:
        async with SessionLocal() as db:
            await seed_catalog(db)
            content = load_curriculum()
            result = await import_curriculum(db, content, apply=True)
            user = await register_user(
                db,
                email=marker["reviewer_email"],
                password=marker["reviewer_password"],
                display_name="Curriculum reviewer",
            )
            marker.update(reviewer_id=str(user.id), curriculum_sha=content_sha(content))
            return result
    finally:
        await engine.dispose()


def prepare(directory: Path, port: int) -> None:
    if directory.resolve() != directory or directory.is_symlink():
        raise ValueError("Preview directory must not use symlinks")
    directory.mkdir(mode=0o700, parents=False, exist_ok=False)
    database = directory / "curriculum-preview.sqlite3"
    descriptor = os.open(database, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(descriptor)
    marker = {
        "kind": "fleng-curriculum-preview-v1",
        "database": database.name,
        "jwt_secret": secrets.token_urlsafe(48),
        "reviewer_email": "reviewer@example.com",
        "reviewer_password": secrets.token_urlsafe(24),
    }
    configure(directory, marker, port)
    # Alembic reads the explicitly isolated child environment, never default DB settings.
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"], cwd=BACKEND, check=True
    )
    result = asyncio.run(populate(marker))
    marker_path = directory / "preview.json"
    descriptor = os.open(marker_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        json.dump(marker, handle, indent=2)
    print(
        json.dumps(
            {
                "directory": str(directory),
                "draft_import": result,
                "credentials_file": str(marker_path),
            },
            indent=2,
        )
    )
    print(f"Login: {marker['reviewer_email']}\nPassword: {marker['reviewer_password']}")


def start(directory: Path, port: int) -> None:
    # Configure before importing application modules or creating their shared engine.
    # Validate the private marker and settings before starting the server.
    marker_path = directory / "preview.json"
    if directory.is_symlink() or marker_path.is_symlink():
        raise ValueError("Preview files must not use symlinks")
    marker = json.loads(marker_path.read_text(encoding="utf-8"))
    configure(directory, marker, port)
    from app.core.config import get_settings
    from app.preview import load_marker, validate_preview_settings

    marker = load_marker(directory)
    validate_preview_settings(get_settings())
    import fcntl

    with (directory / ".server.lock").open("a") as lock:
        os.chmod(directory / ".server.lock", 0o600)
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError("This preview database is already running") from exc
        print(f"Local draft preview: http://127.0.0.1:{port}/courses.html", flush=True)
        print(
            f"Login: {marker['reviewer_email']}\nPassword: {marker['reviewer_password']}",
            flush=True,
        )
        subprocess.run(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app.preview:create_preview_app",
                "--factory",
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
                "--no-proxy-headers",
                "--no-access-log",
            ],
            cwd=BACKEND,
            check=True,
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare", "start"])
    parser.add_argument("--directory", type=Path, default=DEFAULT_DIRECTORY)
    parser.add_argument("--port", type=int, default=3011)
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error("Use an unprivileged port between 1024 and 65535")
    directory = args.directory.expanduser().absolute()
    try:
        if args.action == "prepare":
            prepare(directory, args.port)
        else:
            start(directory, args.port)
        return 0
    except KeyboardInterrupt:
        print("Local preview stopped.")
        return 0
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        # Do not print marker contents, connection strings or external configuration.
        print(
            f"Preview {args.action} failed: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
