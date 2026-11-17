"""The local launcher must serve one checkout and never start a hidden empty database."""

from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

import app as app_package
from app.core.config import Settings
from app.development import (
    CHECKOUT_ROOT,
    checkout_problems,
    create_development_app,
    environment_report,
    primary_checkout,
)


def _settings(**changes) -> Settings:
    return Settings(_env_file=None).model_copy(update=changes)


def _worktree(tmp_path: Path) -> tuple[Path, Path]:
    """A fake main checkout plus a linked worktree whose .git file points at it."""
    main = tmp_path / "main"
    (main / ".git" / "worktrees" / "feature").mkdir(parents=True)
    (main / "backend" / "data").mkdir(parents=True)
    tree = tmp_path / "tree"
    (tree / "backend" / "app").mkdir(parents=True)
    (tree / ".git").write_text(f"gitdir: {main}/.git/worktrees/feature\n")
    return main, tree


def test_linked_worktree_is_detected_and_main_checkout_is_not(tmp_path: Path) -> None:
    main, tree = _worktree(tmp_path)
    assert primary_checkout(tree) == main
    assert primary_checkout(main) is None  # .git is a directory
    assert primary_checkout(tmp_path / "no-git") is None


def test_this_checkout_serves_its_own_code_and_frontend() -> None:
    assert Path(app_package.__file__).resolve().is_relative_to(CHECKOUT_ROOT / "backend")
    report = environment_report(_settings())
    assert any(line == f"Frontend:   {CHECKOUT_ROOT / 'frontend'}" for line in report)


def test_worktree_with_missing_database_is_refused_with_a_remedy(tmp_path: Path) -> None:
    main, tree = _worktree(tmp_path)
    fresh = tree / "backend" / "data" / "fleng.db"
    settings = _settings(database_url=f"sqlite+aiosqlite:///{fresh}")
    problems = checkout_problems(
        settings, root=tree, imported_app=tree / "backend" / "app" / "__init__.py", environ={}
    )
    assert len(problems) == 1
    assert "EMPTY database" in problems[0] and str(main / "backend/data/fleng.db") in problems[0]
    # Explicit opt-in or an existing database are accepted.
    assert not checkout_problems(
        settings,
        root=tree,
        imported_app=tree / "backend" / "app" / "__init__.py",
        environ={"FLENG_ALLOW_NEW_DB": "1"},
    )
    shared = main / "backend" / "data" / "fleng.db"
    shared.write_bytes(b"")
    assert not checkout_problems(
        _settings(database_url=f"sqlite+aiosqlite:///{shared}"),
        root=tree,
        imported_app=tree / "backend" / "app" / "__init__.py",
        environ={},
    )


def test_main_checkout_may_create_its_first_database(tmp_path: Path) -> None:
    root = tmp_path / "clone"
    (root / ".git").mkdir(parents=True)
    (root / "backend" / "app").mkdir(parents=True)
    settings = _settings(database_url=f"sqlite+aiosqlite:///{root / 'backend/data/new.db'}")
    assert not checkout_problems(
        settings, root=root, imported_app=root / "backend" / "app" / "__init__.py", environ={}
    )


def test_code_or_frontend_from_another_checkout_is_refused(tmp_path: Path) -> None:
    main, tree = _worktree(tmp_path)
    shared = main / "backend" / "data" / "fleng.db"
    shared.write_bytes(b"")
    settings = _settings(
        database_url=f"sqlite+aiosqlite:///{shared}", frontend_dir=str(main / "frontend")
    )
    problems = checkout_problems(
        settings, root=tree, imported_app=main / "backend" / "app" / "__init__.py", environ={}
    )
    assert any("imported from" in p for p in problems)
    assert any("FRONTEND_DIR" in p for p in problems)


def test_report_never_prints_secrets() -> None:
    settings = _settings(database_url="sqlite+aiosqlite:///./data/fleng.db")
    text = "\n".join(environment_report(settings))
    assert "secret" not in text.lower() and "password" not in text.lower()
    assert "contents never printed" in text


async def test_dev_server_identifies_its_checkout(monkeypatch, tmp_path: Path) -> None:
    settings = _settings(
        database_url=f"sqlite+aiosqlite:///{tmp_path / 'dev.db'}", frontend_dir=None
    )
    monkeypatch.setattr("app.development.get_settings", lambda: settings)
    monkeypatch.setattr("app.main.get_settings", lambda: settings)
    monkeypatch.setattr("app.development.checkout_problems", lambda *_a, **_k: [])
    app = create_development_app()
    async with AsyncClient(
        transport=ASGITransport(app=app, client=("127.0.0.1", 1)), base_url="http://127.0.0.1:3001"
    ) as client:
        response = await client.get("/")
    assert response.headers["x-fleng-checkout"] == str(CHECKOUT_ROOT)


def test_factory_refuses_an_unsafe_launch(monkeypatch, tmp_path: Path) -> None:
    settings = _settings(database_url=f"sqlite+aiosqlite:///{tmp_path / 'dev.db'}")
    monkeypatch.setattr("app.development.get_settings", lambda: settings)
    monkeypatch.setattr("app.development.checkout_problems", lambda *_a, **_k: ["boom"])
    with pytest.raises(ValueError, match="Unsafe development launch"):
        create_development_app()
