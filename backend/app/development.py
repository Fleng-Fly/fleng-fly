"""Loopback-only npm dev entry point: persistent local drafts, existing learner accounts."""

import os
import sys
import tempfile
from collections.abc import Mapping
from pathlib import Path

from sqlalchemy.engine import make_url

import app as app_package
from app.core.config import BACKEND_ROOT, Settings, get_settings

CHECKOUT_ROOT = BACKEND_ROOT.parent
ALLOW_NEW_DATABASE = "FLENG_ALLOW_NEW_DB"


def primary_checkout(root: Path = CHECKOUT_ROOT) -> Path | None:
    """The main checkout when `root` is a linked git worktree, else `None`.

    A linked worktree has a `.git` *file* ("gitdir: <main>/.git/worktrees/<name>").
    """
    marker = root / ".git"
    if not marker.is_file():
        return None
    first = marker.read_text(encoding="utf-8", errors="replace").splitlines()[:1]
    if not first or not first[0].startswith("gitdir:"):
        return None
    gitdir = Path(first[0].split(":", 1)[1].strip())
    if not gitdir.is_absolute():
        gitdir = root / gitdir
    # <main>/.git/worktrees/<name> -> <main>
    return gitdir.resolve().parents[2]


def _sqlite_file(settings: Settings) -> Path | None:
    url = make_url(settings.database_url)
    if url.drivername != "sqlite+aiosqlite" or not url.database or url.database == ":memory:":
        return None
    return Path(url.database)


def _inside(path: Path, directory: Path) -> bool:
    return path.resolve().is_relative_to(directory.resolve())


def checkout_problems(
    settings: Settings,
    *,
    root: Path = CHECKOUT_ROOT,
    imported_app: Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> list[str]:
    """Reasons this launch could silently mix checkouts or start a new empty database."""
    env: Mapping[str, str] = os.environ if environ is None else environ
    problems: list[str] = []
    code = Path(imported_app if imported_app is not None else app_package.__file__).resolve()
    if not _inside(code, root / "backend"):
        problems.append(
            f"The backend code is imported from {code.parent}, not from this checkout ({root}). "
            "Run from the checkout's backend/ directory and do not install `app` into the "
            "virtualenv in editable mode."
        )
    if settings.frontend_dir:
        frontend = Path(settings.frontend_dir).expanduser()
        if not frontend.is_absolute():
            frontend = Path.cwd() / frontend
        if not _inside(frontend, root):
            problems.append(
                f"FRONTEND_DIR ({frontend}) is outside this checkout ({root}). Unset it so the "
                "frontend of this checkout is served."
            )
    database = _sqlite_file(settings)
    if (
        database is not None
        and not database.exists()
        and (checkout := primary_checkout(root)) is not None
        and env.get(ALLOW_NEW_DATABASE) != "1"
    ):
        problems.append(
            f"This is a linked git worktree and its database {database} does not exist, so a "
            "new EMPTY database (no accounts, no progress) would be created. To use your "
            f"existing data, set DATABASE_URL to the main checkout's file, for example "
            f"sqlite+aiosqlite:///{checkout / 'backend/data/fleng.db'} . "
            f"For an intentionally fresh database set {ALLOW_NEW_DATABASE}=1."
        )
    return problems


def environment_report(settings: Settings, *, root: Path = CHECKOUT_ROOT) -> list[str]:
    """Human-readable launch facts. Never prints environment-file contents or secrets."""
    database = _sqlite_file(settings)
    frontend = (
        Path(settings.frontend_dir).expanduser() if settings.frontend_dir else root / "frontend"
    )
    env_files = [str(path) for path in (BACKEND_ROOT / ".env", root / ".env") if path.is_file()]
    worktree = primary_checkout(root)
    state = (
        "none"
        if database is None
        else ("existing" if database.exists() else "NEW (will be created)")
    )
    return [
        f"Checkout:   {root}" + (f" (linked worktree of {worktree})" if worktree else ""),
        f"Backend:    {BACKEND_ROOT}",
        f"Frontend:   {frontend}",
        f"APP_ENV:    {settings.app_env}",
        f"SQLite:     {database if database else 'not a local SQLite file'} [{state}]",
        f"Env files:  {', '.join(env_files) if env_files else 'none'} (contents never printed)",
        f"URL:        http://127.0.0.1:{settings.port}",
    ]


def validate_checkout(settings: Settings) -> None:
    problems = checkout_problems(settings)
    if problems:
        raise ValueError("Unsafe development launch:\n- " + "\n- ".join(problems))


def validate_development_settings(settings: Settings) -> Path:
    url = make_url(settings.database_url)
    if settings.app_env != "development" or settings.render_external_url:
        raise ValueError("Draft development requires a local development environment")
    if url.drivername != "sqlite+aiosqlite" or not url.database or url.database == ":memory:":
        raise ValueError("Draft development requires a persistent local SQLite database")
    return Path(url.database)


def main() -> None:
    settings = get_settings()
    try:
        database = validate_development_settings(settings)
        validate_checkout(settings)
    except ValueError as error:
        # A readable refusal, not a traceback: nothing was backed up, migrated or created.
        print(f"Fleng did not start.\n{error}", file=sys.stderr, flush=True)
        raise SystemExit(1) from None
    print("\n".join(["Fleng local development", *environment_report(settings)]), flush=True)
    if database.exists():
        from app.db.backup import backup_sqlite

        directory = Path(tempfile.mkdtemp(prefix="fleng-before-dev-"))
        backup = directory / "fleng.sqlite3"
        backup_sqlite(database, backup)
        print(f"Local database backup: {backup}", flush=True)
    from app.db.prepare import main as prepare_database

    prepare_database()


def create_development_app():
    validate_development_settings(get_settings())
    validate_checkout(get_settings())
    from fastapi import Request
    from starlette.middleware.trustedhost import TrustedHostMiddleware
    from starlette.responses import JSONResponse

    from app.main import create_app
    from app.preview import preview_router

    # Ordinary learner authentication/ownership still applies; only this local factory
    # opts into draft reads. The separate private reviewer retains its UUID restriction.
    app = create_app(local_preview_router=preview_router(None))
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "[::1]"])

    @app.middleware("http")
    async def loopback_only(request: Request, call_next):
        if request.client is None or request.client.host not in {"127.0.0.1", "::1"}:
            return JSONResponse(
                {"error": {"code": "FORBIDDEN", "message": "Local development only"}},
                status_code=403,
            )
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Fleng-Mode"] = "local-development-drafts"
        # Lets `npm run dev` say which checkout already owns a busy port (loopback-only server).
        response.headers["X-Fleng-Checkout"] = str(CHECKOUT_ROOT)
        return response

    return app


if __name__ == "__main__":
    main()
