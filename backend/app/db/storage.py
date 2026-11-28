"""Reject hosted SQLite paths whose files disappear with a Render instance."""

from pathlib import Path

from sqlalchemy.engine import make_url

from app.core.config import Settings


class DatabaseConfigurationError(RuntimeError):
    """Safe operator-facing error; messages must never contain connection secrets."""


def validate_render_storage(settings: Settings) -> None:
    if not settings.is_production or not settings.render_external_url:
        return
    url = make_url(settings.database_url)
    if url.get_backend_name() != "sqlite":
        return
    mount = Path("/var/data")
    if (
        url.database
        and url.database != ":memory:"
        and Path(url.database).resolve().is_relative_to(mount.resolve())
        and mount.is_mount()
    ):
        return
    raise DatabaseConfigurationError(
        "Render SQLite is on ephemeral storage: accounts and progress disappear on sleep/redeploy. "
        "Set DATABASE_URL to an external PostgreSQL database. SQLite is accepted only beneath "
        "an actually mounted persistent disk at /var/data. No database was reset or moved."
    )
