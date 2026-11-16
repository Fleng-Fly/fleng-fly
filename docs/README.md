# Fleng developer documentation

Fleng is an English-learning modular monolith. Python/FastAPI serves REST/JSON under /api/v1 and plain HTML/CSS/JavaScript. SQLAlchemy async/Alembic support local SQLite and optional PostgreSQL; Pydantic defines contracts. JWT access tokens and rotating cookie refresh sessions authenticate users. Node runs repository tooling, not a backend/frontend build.

## Capability status

| Status | Scope |
| --- | --- |
| Implemented | Auth/settings/reset API, published catalog, graded lessons, once-only XP/progress, vocabulary/reviews, flashcard session backend, streaks/achievements/leaderboard, OpenRouter/history/SSE and floating assistant |
| Draft | Five A0–B2 courses, 50 lessons, 500 course words, 400 exercises; ordinary catalog hides unpublished content |
| Experimental | Narrow linguistic heuristics, optional evidence/AI review; local reviewer tooling is development-only |
| Planned | Dedicated Vocabulary/Flashcards/AI Tutor/reset UI, separate vocabulary test grading, adaptive SRS and numeric progression |
| Unverified | Live PostgreSQL, current hosting/proxy/cookies, real OpenRouter/SMTP and production restore |

Implementation does not imply production readiness; structural curriculum checks do not prove linguistic correctness.

## Documentation navigation

- [Getting started](01-getting-started/README.md)
- [Architecture](02-architecture/README.md)
- [Backend](03-backend/README.md)
- [Frontend](04-frontend/README.md)
- [Database](05-database/README.md)
- [Learning system](06-learning/README.md)
- [AI system](07-ai/README.md)
- [Security](08-security/README.md)
- [Deployment](09-deployment/README.md)
- [Testing](10-testing/README.md)
- [Contributing](11-contributing/README.md)
- [Reference](12-reference/README.md)

## Quick start

Requires Python 3.11+ and Node.js 20+. From repository root:

```sh
npm run dev
```

Open http://localhost:3001/; /docs is interactive API documentation. The launcher prepares file-backed SQLite and seeds only an empty legacy catalog. No separate frontend server/build. Preserve existing .env files. See [installation](01-getting-started/installation.md) and [configuration](01-getting-started/configuration.md).

## Architecture and workflow

Browser fetch calls relative API routes; backend services enforce identity, ownership, grading and persistence. Provider keys stay backend-only. Netlify is optional static hosting with a disabled checked-in API proxy. See [system overview](02-architecture/system-overview.md) and [data flows](02-architecture/data-flow.md).

Read AGENTS.md, preserve existing work, use the current stack, test, independently review and update docs/map/plans. [Contributing](11-contributing/README.md) describes normal logical commits; this task explicitly leaves work uncommitted.

## Testing and operational boundaries

Run npm backend:test/backend:lint/backend:typecheck and the documented Node/migration/curriculum checks. [Testing](10-testing/README.md) provides commands; [dated validation](12-reference/validation-report.md) separates current evidence from historical counts.

Read [security](08-security/README.md) before auth/ownership changes and [deployment](09-deployment/README.md) before release. Ephemeral SQLite can lose learner data; old JWTs remain valid until expiry after session revocation. [Known limitations](12-reference/known-limitations.md) identifies UI/pedagogical/integration gaps.

Existing documents remain at original URLs; [preservation register](12-reference/documentation-migration.md) maps every old document and stale statements. Source is authoritative.
