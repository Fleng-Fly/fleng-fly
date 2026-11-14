# Content publication

Source: backend/app/db/content/curriculum-a0-b2.json. From backend/:

```sh
.venv/bin/python -m app.db.curriculum --validate-only
.venv/bin/python -m app.db.curriculum --help
```

--validate-only checks without DB and prints canonical SHA. No write flags means DB dry-run. For an explicitly disposable review path:

```sh
DATABASE_URL=sqlite+aiosqlite:////tmp/fleng-content-review.db .venv/bin/alembic upgrade head
DATABASE_URL=sqlite+aiosqlite:////tmp/fleng-content-review.db .venv/bin/python -m app.db.curriculum
DATABASE_URL=sqlite+aiosqlite:////tmp/fleng-content-review.db .venv/bin/python -m app.db.curriculum --apply-draft
```

Confirm the path before writes. Re-import preserves publication state and rejects conflicting content/IDs before mutation. SQLite startup now imports and publishes the exact owner-authorized curriculum
release described below, including production SQLite preparation. Normal public
routes expose those published rows; unrelated/unapproved drafts remain hidden. See [default local workflow](local-draft-workflow.md).

After teacher/translator review, --publish-reviewed-sha acknowledges the exact canonical SHA in a review environment; it is not proof/signature of approval. CLI rejects production writes. The owner has now authorized the exact release below. Future content changes need
a new explicit release approval. Raw-file SHA for normalization and canonical publication SHA differ; content edits need renewed review rather than overwriting submitted exercises.

[Section index](README.md) · [Documentation home](../README.md)

## Owner-authorized release — 2026-11-14

The owner explicitly requested publication of all five A0–B2 courses. SQLite
preparation now promotes the five courses and all 50 lessons for this exact
canonical content SHA:

`27ab5cdc8cdadbfc85353cea58fc2584459c130aea460cf391a2e5d67b108013`

The startup approval is pinned in `app/db/prepare.py`; changed content fails SHA
validation rather than inheriting publication permission. The importer distinguishes
`owner_authorized` publication from `reviewed` publication. Linguistic/editorial
review remains incomplete and the JSON source status remains draft; publication
does not certify CEFR, translations or licensing review. Ordinary imports without
an approval SHA still create drafts and never unpublish already released rows.

After `python run.py`, the ordinary public API exposes all seven courses, the 50
A0–B2 lessons and their 500 course words. New and existing SQLite catalogs use
the same idempotent path; existing account IDs, XP/progress and unrelated courses
are preserved. No broad publish-all SQL or authentication bypass is used.
PostgreSQL startup remains an explicit separate release path. No live Render
deployment/push is performed by committing this change.
