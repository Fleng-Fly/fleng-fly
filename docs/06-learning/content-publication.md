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

Confirm the path before writes. Re-import preserves publication state and rejects conflicting content/IDs before mutation. Production startup never runs it. The guarded loopback-only npm dev launcher
imports unpublished drafts for existing local learner accounts; it never sets
publication flags. See [default local workflow](local-draft-workflow.md).

After teacher/translator review, --publish-reviewed-sha acknowledges the exact canonical SHA in a review environment; it is not proof/signature of approval. CLI rejects production writes. Production promotion needs separate backup/release approval. Raw-file SHA for normalization and canonical publication SHA differ; content edits need renewed review rather than overwriting submitted exercises.

[Section index](README.md) · [Documentation home](../README.md)
