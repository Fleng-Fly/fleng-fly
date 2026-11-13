# Backend tests

From root:

```sh
npm run backend:test -- -q
```

Focused checks from backend/:

```sh
.venv/bin/pytest -q tests/test_auth.py tests/test_auth_origins.py
.venv/bin/pytest -q tests/test_exercises.py tests/test_progress.py
.venv/bin/pytest -q tests/test_vocabulary_flashcards.py
.venv/bin/pytest -q tests/test_ai.py tests/test_ai_security.py tests/test_ai_provider.py
```

conftest.py injects AsyncSession into httpx ASGITransport. Default fixtures create real in-memory SQLite ORM tables/FKs; other tests use temporary file DBs/processes for migrations/concurrency/restarts. Provider/SMTP tests inject synthetic behavior, not paid services.

PostgreSQL tests explicitly skip without TEST_DATABASE_URL. Skips are not passes. [Dated validation](../12-reference/validation-report.md) records this run rather than a permanent test count.

[Section index](README.md) · [Documentation home](../README.md)
