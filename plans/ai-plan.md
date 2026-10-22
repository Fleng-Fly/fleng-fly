# AI and backend completion plan

Status at 2026-10-18:

- **Completed:** architectural/Git audit; preserve incoming changes and frontend design.
- **Completed:** compose loopback binding, native PostgreSQL instructions, connectivity
  helper, one valid migration chain and offline PostgreSQL SQL compilation.
- **Completed:** vocabulary/review history, daily streak policy, deterministic
  achievements, authenticated profile PATCH, secure SMTP-capable password reset.
- **Completed:** async OpenRouter adapter, server configuration/limits, tutor,
  conversations/history/delete, grammar explanation, validated practice generation.
- **Completed:** deterministic recommendations, optional incremental SSE,
  persistent rate/budget/concurrency reservations, bounded inputs/history/output.
- **Completed:** mocked provider and ORM/API tests, Ruff/mypy, independent self-review,
  documentation and project map updates.
- **Blocked by infrastructure:** real PostgreSQL migration/registration/auth/XP/
  persistence verification. Docker/PostgreSQL tools absent, localhost:5432 refuses
  IPv4/IPv6 connections. No runtime SQLite substitution.
- **Blocked by infrastructure/credentials:** manual paid OpenRouter integration
  with a real configured model/key and database. Tests never use paid requests.
- **Next:** start PostgreSQL using docs/development.md, migrate and seed development
  catalog, run TEST_DATABASE_URL suite, configure SMTP inbox and OpenRouter,
  complete the documented manual integration checks.
- **Next:** wire existing frontend pages to new APIs in a separate UI task; advanced
  SRS, full mistake-attempt history, speaking and subscriptions remain future work.
- **Commits:** intentionally not created; user explicitly prohibited automatic commits.

Implementation and limitations are specified in docs/ai.md and docs/development.md.
