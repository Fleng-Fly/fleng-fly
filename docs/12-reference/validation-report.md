# Documentation audit and validation — 2026-11-13

## Outcome and scope

All twelve requested sections are populated and linked from [docs/README.md](../README.md). This is ordinary GitHub-compatible Markdown; no documentation site/server, framework, dependency or build system was added. Source behavior was not changed.

**136 documentation Markdown files:** 107 newly created, 29 existing preserved. No existing document was moved/deleted/overwritten. New navigation consolidates current behavior while retaining operational reports at their original URLs. [Preservation register](documentation-migration.md) maps every existing document to its current section and accuracy caveats. No required section is left empty or missing.

Runtime used: Python 3.14.10 and Node.js v26.12.1. Declared minimums remain Python 3.11 and Node.js 20; those minimum-version environments were not separately run.

## Current validation results

| Check | Observed result |
| --- | --- |
| Full pytest via npm run backend:test -- -q | **377 passed, 15 skipped, 12 warnings**, 71.94s |
| Ruff app/tests | Passed |
| mypy app | Passed, 77 source files |
| New documentation checker Ruff using backend config | Passed |
| Node course DOM | 7 passed |
| Node AI API | 3 passed |
| Node SSE parser | 7 passed |
| Node assistant widget | 10 passed |
| Local Markdown link/anchor check | Passed: 136 Markdown files, 575 local links/anchors; zero failures |
| Runtime API/schema/model/config/example contracts | 42 operations, 47 named schemas, 21 models, 48 Settings fields, 49 examples validated |
| Temporary SQLite Alembic upgrade/current/check | Passed; head 20261110_1400, no new upgrade operations |
| PostgreSQL full offline SQL | Compiled through current head; no connection |
| Full launcher/stabilization smoke | Passed: npm dev, production launcher, static/readiness, cookies/origins, refresh/reuse/password/logout, lessons/once-only XP and restart persistence |
| Curriculum importer --validate-only | Passed: five courses/50 lessons and canonical SHA |
| Curriculum validator --all | Exit 0: 5 courses/50 lessons/500 words/400 exercises structurally valid; 2 medium advisories, 107 informational entries |
| Curriculum A0 Markdown report | Generated successfully in temporary output |
| Validator --check-sources | **Exit 1 expected unavailable evidence**, not linguistic verification |
| Source/preview/browser/importer CLI help | Checked |
| Existing AI secret audit | 212 working files plus Git index, zero concrete OpenRouter findings |
| New documentation secret-pattern review | No confirmed secret; retained legacy development URL uses a password placeholder |
| Shell blocks in numbered guides | 67 parsed with bash -n; zero syntax failures |
| git diff --check | Passed |
| Mermaid | Eight diagrams manually checked for implementation/cardinality/fences; no mmdc/parser available, render not verified |

Pytest's 15 skipped cases require a dedicated PostgreSQL TEST_DATABASE_URL. Warnings include existing httpx/Starlette and Alembic deprecations; pytest also emits an unset pytest-asyncio fixture-loop-scope warning. A sandbox run stalled on SQLite and was interrupted. Server recovery interrupted result capture of the first unrestricted run; only the completed rerun above is counted. Database tests/migration/smoke use isolated memory/files, not learner/production data.

Linguistic result: **500 source_unavailable words, zero externally verified**, optional AI review not_run. Structural exit 0 does not approve publication. Canonical SHA is an acknowledgement of content identity, not evidence of expert review.

## Reproducible validation commands

From repository root:

```sh
python3 scripts/check-docs.py
backend/.venv/bin/python scripts/check-docs.py --contracts
npm run backend:test -- -q
npm run backend:lint
npm run backend:typecheck
backend/.venv/bin/ruff check --config backend/pyproject.toml scripts/check-docs.py
node --experimental-vm-modules scripts/test-courses.mjs
node --experimental-vm-modules scripts/test-ai-api.mjs
node --experimental-vm-modules scripts/test-ai-stream.mjs
node --experimental-vm-modules scripts/test-ai-widget.mjs
backend/.venv/bin/python scripts/validate_curriculum.py --all
backend/.venv/bin/python scripts/validate_curriculum.py --check-sources
python3 scripts/backend-stabilization-smoke.py
python3 scripts/audit-ai-secrets.py
git diff --check
```

Use the [migration check instructions](../10-testing/migration-tests.md) with a new disposable filename. The completed SQLite check used /tmp/fleng-doc-audit-migrations-20261113.db; PostgreSQL offline compilation used a synthetic localhost URL and did not connect. npm run dev and backend/run.py were exercised by the existing temporary-data smoke runner.

Installation/pip, Docker startup, migration creation, explicit user-content imports/publication, production deployment and paid AI/SMTP commands were checked against manifests/source and shell syntax where present, but were **not executed against application/production state**. Existing environment already had dependencies; reinstallation was unnecessary. Individual curl examples use synthetic records and are schema/syntax examples, not proof every shown UUID exists. Endpoint behaviors are exercised by the full API suite. Windows parity remains unverified.

## Checker scope

scripts/check-docs.py uses Python standard library for local inline/reference Markdown targets, anchors, empty documents and fence balance. --contracts uses the backend venv to compare ordinary OpenAPI operations, complete named schemas, ORM column types/nullability, Settings key inventory and Pydantic request/response examples. It disables .env loading and selects an in-memory inspection configuration without issuing DB/network calls. It does not parse all possible Markdown extensions, validate external URLs, prove every service permission/error path, or replace a Mermaid renderer.

Four links initially pointed to the not-yet-created validation report; creating the final report resolved them. No broken link in the retained documents was found by this checker. Final link totals are reported after this file is written; counts can grow when navigation changes.

## Independent self-review and corrections

Review after writing rechecked schema/runtime assumptions, security boundaries, draft visibility, preservation, command execution scope and duplication. It corrected:

- A generated multiple-choice example missing required valid options.
- A model-name assumption: actual entity is PasswordReset, not PasswordResetToken.
- Self-check semantics: even assessment incorrect completes participation and can award once-only points; it is not objective correctness.
- Study minutes are estimated lesson duration credited on first completion, not measured browser time.
- Nullable lesson/refresh-successor ER cardinalities and empty flashcard example status.
- Compose environment semantics: user/password/database are local fixed examples; only POSTGRES_PORT is host-interpolated.
- A checker iteration incompatible with current FastAPI included-router wrappers; examples now resolve named runtime schemas to real Pydantic classes and assert nonzero validation.

The audit also reproduced a real existing Settings bug: sqlite+aiosqlite:///:memory: duplicates its driver name. sqlite:///:memory: works for Settings inspection; production preparation rejects memory DBs. This is documented without changing application logic. Historical contradictions (migration head, old feature checkboxes/counts, body-limit/anti-enumeration claims, host/proxy statements) are listed in the [preservation register](documentation-migration.md).

## API routes documented

All ordinary registered operations are listed below. Generated Swagger/ReDoc/OpenAPI, static files, unknown-/api fallback and local preview overrides are documented separately and not counted as product operations.

- `GET /api/v1/health`
- `GET /api/v1/health/ready`
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `GET /api/v1/users/me`
- `PATCH /api/v1/users/me`
- `POST /api/v1/users/me/password`
- `GET /api/v1/progress/me`
- `GET /api/v1/courses`
- `GET /api/v1/courses/{slug}`
- `GET /api/v1/lessons/{slug}`
- `POST /api/v1/lessons/{slug}/start`
- `GET /api/v1/lessons/{slug}/progress`
- `POST /api/v1/lessons/{slug}/submit`
- `GET /api/v1/vocabulary/course-words`
- `POST /api/v1/vocabulary/flashcards/sessions`
- `GET /api/v1/vocabulary/flashcards/sessions/{session_id}`
- `POST /api/v1/vocabulary/flashcards/sessions/{session_id}/complete`
- `GET /api/v1/vocabulary/flashcards/sessions/{session_id}/test-words`
- `GET /api/v1/vocabulary/stats`
- `GET /api/v1/vocabulary`
- `POST /api/v1/vocabulary`
- `PATCH /api/v1/vocabulary/{item_id}`
- `DELETE /api/v1/vocabulary/{item_id}`
- `POST /api/v1/vocabulary/{item_id}/review`
- `GET /api/v1/vocabulary/{item_id}/reviews`
- `GET /api/v1/streaks/me`
- `GET /api/v1/achievements/me`
- `GET /api/v1/leaderboard`
- `POST /api/v1/auth/password-reset/request`
- `POST /api/v1/auth/password-reset/confirm`
- `GET /api/v1/ai/status`
- `POST /api/v1/ai/chat`
- `GET /api/v1/ai/conversations`
- `GET /api/v1/ai/conversations/{conversation_id}`
- `DELETE /api/v1/ai/conversations/{conversation_id}`
- `POST /api/v1/ai/explain`
- `POST /api/v1/ai/generate-exercise`
- `GET /api/v1/ai/recommendations`
- `POST /api/v1/ai/chat/stream`

## Database entities documented

`AIConversation`, `AIMessage`, `AIUsage`, `Achievement`, `Course`, `CourseVocabularyItem`, `Exercise`, `ExerciseSubmission`, `FlashcardSession`, `LearningActivity`, `Lesson`, `LessonProgress`, `PasswordReset`, `Profile`, `Progress`, `RefreshToken`, `RequestLimit`, `User`, `UserAchievement`, `VocabularyItem`, `VocabularyReview`.

Columns, PKs, FKs, nullable types, unique/CHECK constraints and indexes are in [schema](../05-database/schema.md); responsibilities/ER cardinalities are in [relationships](../05-database/relationships.md). Flashcard word references are deliberately JSON snapshots without FK edges. Curriculum goals/prerequisites remain source metadata rather than invented DB tables.

## Diagrams

Eight Mermaid blocks: high-level system, frontend/API/DB, authentication sequence, course learning, vocabulary/flashcard handoff, curriculum validation/import/review, AI streaming sequence and complete FK ER view. They reflect current modular-monolith boundaries. Mermaid rendering remains not run because no parser/renderer was available.

## Existing documents and new files

No physical migration was needed: all original file URLs remain valid. The preservation register contains all 29 existing files and reuse decisions. New Markdown files are enumerated by the tree below (main README and numbered subdirectories); original documents are the root files other than README. Supporting additions are scripts/check-docs.py, project-map/documentation.md and plans/documentation.md. Root README.md and project-map/README.md gain navigation links; pre-existing source/docs/plan changes are preserved.

## Documentation directory tree

```text
docs/
├── 01-getting-started/
│   ├── README.md
│   ├── configuration.md
│   ├── development.md
│   ├── installation.md
│   ├── prerequisites.md
│   ├── troubleshooting.md
├── 02-architecture/
│   ├── README.md
│   ├── backend-architecture.md
│   ├── data-flow.md
│   ├── frontend-architecture.md
│   ├── module-dependencies.md
│   ├── request-lifecycle.md
│   ├── system-overview.md
├── 03-backend/
│   ├── README.md
│   ├── ai-api.md
│   ├── api-overview.md
│   ├── api-schemas.md
│   ├── application-lifecycle.md
│   ├── authentication-api.md
│   ├── catalog-api.md
│   ├── domain-errors.md
│   ├── error-handling.md
│   ├── exercises-api.md
│   ├── flashcards-api.md
│   ├── gamification-api.md
│   ├── health-api.md
│   ├── leaderboard-api.md
│   ├── lessons-api.md
│   ├── progress-api.md
│   ├── users-api.md
│   ├── vocabulary-api.md
├── 04-frontend/
│   ├── README.md
│   ├── api-integration.md
│   ├── authentication-flow.md
│   ├── frontend-architecture.md
│   ├── pages.md
│   ├── responsive-design.md
│   ├── state-management.md
│   ├── styling.md
├── 05-database/
│   ├── README.md
│   ├── data-integrity.md
│   ├── migrations.md
│   ├── postgresql.md
│   ├── relationships.md
│   ├── schema.md
│   ├── seed-data.md
│   ├── sqlite.md
├── 06-learning/
│   ├── README.md
│   ├── content-publication.md
│   ├── courses.md
│   ├── curriculum-a0-b2.md
│   ├── curriculum-preview.md
│   ├── curriculum-validation.md
│   ├── exercises.md
│   ├── flashcards.md
│   ├── grading.md
│   ├── lessons.md
│   ├── progress-and-xp.md
│   ├── vocabulary.md
├── 07-ai/
│   ├── README.md
│   ├── ai-tutor.md
│   ├── architecture.md
│   ├── conversations.md
│   ├── limits-and-errors.md
│   ├── openrouter.md
│   ├── prompts.md
│   ├── streaming.md
├── 08-security/
│   ├── README.md
│   ├── authentication.md
│   ├── authorization.md
│   ├── cookies-and-sessions.md
│   ├── cors-and-origins.md
│   ├── input-validation.md
│   ├── rate-limiting.md
│   ├── secrets-management.md
│   ├── threat-model.md
├── 09-deployment/
│   ├── README.md
│   ├── database-deployment.md
│   ├── environment-variables.md
│   ├── environments.md
│   ├── netlify.md
│   ├── production-checklist.md
│   ├── render.md
│   ├── troubleshooting.md
├── 10-testing/
│   ├── README.md
│   ├── backend-tests.md
│   ├── browser-tests.md
│   ├── curriculum-tests.md
│   ├── database-tests.md
│   ├── frontend-tests.md
│   ├── migration-tests.md
│   ├── quality-gates.md
├── 11-contributing/
│   ├── README.md
│   ├── code-review.md
│   ├── coding-standards.md
│   ├── development-workflow.md
│   ├── documentation-guidelines.md
│   ├── git-workflow.md
│   ├── pull-requests.md
├── 12-reference/
│   ├── README.md
│   ├── api-status-codes.md
│   ├── configuration-reference.md
│   ├── documentation-migration.md
│   ├── glossary.md
│   ├── known-limitations.md
│   ├── validation-report.md
├── README.md
├── ai-assistant-integration.md
├── ai-security-audit.md
├── ai.md
├── api.md
├── architecture.md
├── authentication.md
├── backend-completion-report.md
├── backend-stabilization-report.md
├── backend.md
├── courses-implementation.md
├── curriculum-a0-b2.md
├── curriculum-content-quality.md
├── curriculum-sources-and-licenses.md
├── curriculum-validation-report.md
├── curriculum-validator.md
├── curriculum-visual-review.md
├── database.md
├── deployment.md
├── development.md
├── frontend.md
├── leaderboard-hosting-report.md
├── local-postgres-verification.md
├── render-https-origin-403.md
├── render-registration-origin-403.md
├── render-sqlite-registration-diagnostics.md
├── render-sqlite-startup.md
├── security.md
├── testing.md
├── vocabulary-flashcards-api.md
```

## Remaining gaps and unverified operations

No requested documentation section is unpopulated. External operational claims remain deliberately unverified: live PostgreSQL/asyncpg integration, current Netlify/Render dashboard/deployed revision/public responses, production TLS/proxy/cookie/SSE behavior, paid OpenRouter, real SMTP, backup/restore, Windows parity, fresh browser visual/accessibility QA and Mermaid rendering. Old screenshots/reports are explicitly historical.

Human teaching/translation review, source-cache licensing/evidence enrichment and separately approved release remain necessary before draft publication. Missing dedicated UI and separate vocabulary testing integration are product gaps documented as such, not falsely marked complete. Existing historical plans still contain stale stage checkboxes; the register/current guides explain precedence while preserving that evidence.

## Security and Git safety

No secrets, real reviewer passwords, private user rows or provider keys are included. Secret scans are pattern/specific-key checks, not a universal credential-leak guarantee. No .env was copied; generated preview credentials remain private. No application logic/source change, production write, publication, deployment, push, reset/clean, amend, author change or automatic commit was performed.

Git working tree remains dirty by design: existing backend/frontend/curriculum/report/plan changes predate this task; new documentation and the lightweight checker are unstaged. Normal project logical-commit guidance is superseded here by the explicit request not to commit automatically. Review status before staging and keep unrelated work separate.

Final status snapshot: **31 tracked modified paths, 156 untracked files** as reported by git status. Nothing staged. Only README.md and project-map/README.md among tracked files were changed by this documentation task; all other tracked modifications were present at initial audit.
