# Milestones & Status

Integration (2026-11-14): `projectenglich` learning interactions, PWA and desktop
sources merged with current curriculum/flashcards. Legacy desktop revision
collision handled by migration `20261114_1200`; Windows tooling adapted and copied
development database prepared. No push/deploy. Validation and remaining platform
limits: [integration report](../docs/projectenglich-integration.md).

Presentation readiness (2026-10-24): local SQLite migration head and seeded
catalog verified; three fictional accounts seeded through auth and grading;
HTTP login/catalog/lesson/XP/restart checks passed. Browser inspection remains
unverified because no browser surface was available in this session. See
`DEMO.md`. Next: present the existing learning flow; no new feature milestone
was started.
The `npm run demo` wrapper was verified both against an existing server and
from a cold start; it leaves the server running after successful checks.
`./start.sh` is the presentation entry point and passed a cold-start check.

> Living status board. Keep in sync with `plans/roadmap.md` and the actual repo.
> Legend: ✅ completed · 🚧 in progress · ⛔ blocked · ⬜ next/not started ·
> ❌ cancelled.

Last updated: M4 — catalog + graded lesson flow (exercises, submissions, XP,
lesson/course progress) landed; Phase A (static frontend served by FastAPI)
complete.

Frontend update (2026-10-22): Dashboard and Lessons UI phases are complete
against the available written design brief. Lessons uses the live lesson,
progress, submission and lesson-filtered vocabulary APIs. Firefox smoke covers
1440/768/360 widths, session restore, tabs, submission and navigation. Exact
Figma screenshot comparison is pending; Login/Sign Up is the next UI phase.

| # | Milestone | Status | Notes |
| - | --------- | ------ | ----- |
| M0 | Repository foundation (docs, map, plans, design) | ✅ completed | |
| M1 | Frontend + FastAPI backend vertical slice | ✅ completed | pnpm workspace, FastAPI, SQLAlchemy/Alembic, health + users, Next.js status indicator |
| M2 | Identity + auth storage | ✅ completed | `User`, `Profile`, `RefreshToken`, `Progress`; argon2id; migration `20261005_1000` |
| M3 | Authentication & progress API + frontend session | ✅ completed | register/login/refresh/logout, read-only `/users/me`, `/progress/me` |
| M3a | Phase A: static frontend served by FastAPI | ✅ completed | Next.js removed; `frontend/` HTML/CSS/JS; landing/login/register/dashboard/settings; same-origin CSRF fix |
| M4 | Catalog & learning | ✅ completed | courses/lessons read API; `single_choice`/`text`/`self_check` exercises with server-side grading; lesson start/submit/progress; once-only XP; per-course progress; lesson page + dashboard |
| M5 | Vocabulary + SRS | 🟡 partial | personal words, reviews and basic 1/7-day scheduling implemented; adaptive SRS deferred |
| M6 | Gamification | 🟡 partial | XP, streaks and achievements implemented; numeric level progression deferred |
| M7 | Frontend MVP | ⬜ | app shell + core screens + design system |
| M8 | AI tutor | 🟡 partial | OpenRouter/SSE/history/explanation/practice APIs implemented; live provider verification and UI pending |
| M9 | Polish & launch | ⬜ | practice depth, notifications, analytics, deploy |

## Known limitations / not yet verified

- **PostgreSQL runtime is unverified in this environment** (no Docker/PostgreSQL
  available). Migrations are verified offline with `pnpm db:sql`; applying them
  to a real PostgreSQL instance and running DB integration tests remain tasks in
  `plans/testing-plan.md`.
- Auth tests use in-memory SQLite, not PostgreSQL.
- Settings profile/email editing and password changes are implemented. Email
  verification and broader authentication follow-ups remain separate work.

## Blocked

Nothing is blocked. The PostgreSQL runtime checks above are environment
limitations, not project blockers.

## Immediate next actions (M5 — Vocabulary + SRS)

1. ✅ M4 complete: catalog, exercises, grading, lesson/progress writes.
2. ⬜ `VocabularyWord`, `UserVocabulary`, `FlashcardReview` + migration; the
   `vocabulary` module and SRS scheduling.
3. ⬜ Gamification (M6): `XpEvent`, `Streak`, `Achievement` on top of lesson
   completion.
4. ⬜ Apply migrations and run the suite against a real PostgreSQL instance in CI.
5. Deferred auth follow-ups: profile editing, email verification, password
   reset, rate limiting.

## Decisions log

| Date | Decision | Rationale |
| ---- | -------- | --------- |
| Foundation | Modular monolith | Simplicity, team consistency (`AGENTS.md` 9) |
| Foundation | PostgreSQL | Relational integrity + JSONB flexibility |
| Foundation | pnpm workspace (frontend) | Efficient JS monorepo without extra tooling |
| M1 | **Backend rewritten in Python / FastAPI** | Explicit product decision; SQLAlchemy 2 async + Alembic + Pydantic |
| M1 | **FastAPI + Python is the only backend stack finalized** | NestJS/Express/TypeScript backend is forbidden; TypeScript stays frontend-only (`AGENTS.md` backend stack rules) |
| M1 | Backend runs in its own virtualenv, orchestrated by root Node scripts | Polyglot repo without adding Turborepo/Nx |
| M1 | Database-unavailable errors map to `503` (including asyncpg `OSError`) | Honest availability signal; keeps `/health` informative |
| M3 | Refresh tokens are opaque random strings stored as SHA-256 hashes (not JWTs) | Nothing to verify client-side; DB lookup by hash; a leak reveals no usable token |
| M3 | `/progress/me` is read-only (no client `PATCH`) | Progress must be server-derived; a client-writable progress endpoint breaks integrity (`docs/security.md`) |
| M3 | Access token stays in memory; refresh token in an HttpOnly cookie | Avoids XSS-exfiltratable long-lived secrets (`localStorage`) |
| M3a | **Frontend replaced with plain HTML/CSS/JS served by FastAPI** | No build step; one deployable; first-party cookies; smaller, understandable UI (`AGENTS.md` 1–2) |
| M3a | Same-origin requests accepted by the CSRF Origin check | Browsers send `Origin` on same-origin POSTs; the static UI shares the API origin |
| M4 | Lesson `slug` is **globally** unique (not per course) | `GET /lessons/{slug}` has no course context; global uniqueness avoids ambiguity |
| M4 | Lesson `theory` is plain text with light markup (`## `, `- `), rendered via `textContent` | Keeps content authoring simple and prevents stored/rendered HTML/XSS |
| M4 | Catalog read endpoints are public; catalog **pages** are behind `requireSession` | Content is not sensitive; the UI stays part of the signed-in learning flow |
| M4 | Lesson-path identifier is the lesson **slug** (e.g. `/lessons/{slug}/submit`) | Consistent with `GET /lessons/{slug}`; no UUID round-trip needed |
| M4 | XP = exercise `points`, awarded **once per exercise** on first completion; no lesson bonus | Bounded, server-side, and impossible to farm with retries |
| M4 | `single_choice`/`text` complete on a correct answer; `self_check` completes on a correct self-assessment | The server cannot objectively grade free text; self-check is explicitly self-assessed |
| M4 | A lesson completes only when it has ≥1 exercise and all are completed | Prevents "opened ⇒ completed"; empty lessons never auto-complete |
| M4 | `exercises_completed` and per-course progress are **derived** on read | No denormalised counters to drift |

## Backend completion checkpoint — 2026-10-18

Implemented: vocabulary, streaks, deterministic achievements, profile PATCH,
password reset, OpenRouter provider/tutor/history/explanation/practice generation,
recommendations, SSE and security limits. Automated mocked/ORM verification is
complete; real PostgreSQL migration/integration and live OpenRouter testing remain
blocked. See ai-plan.md and docs/development.md for exact next steps. These backend
APIs do not imply completed frontend UI integration. Changes are uncommitted by
explicit user instruction.

## Backend stabilization — 2026-10-28

Completed implementation and isolated SQLite checks: refresh atomicity,
login/register limits, nonblocking Argon2, password-session revocation and
concurrent learning updates. The follow-up request authorizes committing this stage and the README update. Live PostgreSQL
is NOT VERIFIED; verification results are in `docs/backend-stabilization-report.md`.


## Floating assistant integration — 2026-11-01

- **Completed:** Dashboard/Lessons reusable widget, owned history selection/new chat,
  incremental UTF-8 SSE, safe text rendering, minimize/close lifecycle.
- **Completed:** authenticated readiness API, published lesson/exercise context,
  request-ID deduplication on existing AIUsage (migration `20261101_1200`).
- **Completed:** mocked backend/parser regression checks, dev-server SQLite smoke,
  independent self-review; docs and project map updated.
- **Next / unverified:** actual browser QA at 360/768/desktop, virtual keyboards,
  paid OpenRouter with a configured model/key, live PostgreSQL integration.
- **Commits:** not created, per explicit user instruction.

Evidence: `docs/ai-assistant-integration.md`. Standalone AI Tutor page remains deferred.


## Leaderboard + hosting preparation — 2026-11-04

- **Completed:** authenticated all-time XP ranking, top-3 cards, learner table,
  own rank, short/empty/loading/error/retry states and responsive styles.
- **Completed:** production launcher/Procfile, environment template, secure-cookie
  and secret guards, exact HTTPS CORS origins, DB readiness and deployment notes.
- **Next:** choose hosting/managed PostgreSQL and supply production secrets;
  apply migrations and verify public HTTPS auth, proxy trust and optional AI.
- **Not verified:** exact Figma comparison (source not supplied), browser layout
  at 360/768/desktop (browser unavailable), live hosting/PostgreSQL/OpenRouter/SMTP.

## Render registration Origin 403 — 2026-11-04

Completed: live 403 traced to auth Origin guard; effective CORS configuration
allows Netlify but omits Render. Production template now lists both; nine
regressions, rejection header diagnostics and HTTP smoke cover TLS termination
without disabling CSRF/CORS. SQLite unchanged. Next: apply CORS_ORIGIN and restart
Render, then repeat public checks; separately configure Netlify API proxy (404).
See `docs/render-registration-origin-403.md` for evidence and check results.

## Render HTTPS Origin follow-up — 2026-11-05

Completed locally: validated Render external HTTPS origin is merged into shared
CORS/auth allowlist; tests cover Netlify-only CORS plus Render runtime environment,
all session endpoints and trusted/untrusted Uvicorn forwarding behavior. Launcher
still overrides platform wildcard proxy trust. Next: deploy commit and verify real
HTTPS registration/session rotation; public post-deploy validation is pending.
Evidence: `docs/render-https-origin-403.md`.

## Vocabulary backend — 2026-11-10

Completed: David's course vocabulary, saved flashcard sets, ownership/completion,
Roma handoff contract and backend verification. Next: frontend integration,
Roma's grading/retries/XP and curated catalog content. A0 course support requires
shared catalog coordination; live PostgreSQL NOT VERIFIED.


## A0–B2 curriculum — 2026-11-10

Completed: A0 migration and full A0–B2 draft content/seed validation. Earlier A0 prerequisite is resolved. Pending: human content approval and production promotion; existing legacy content is retained. See docs/curriculum-a0-b2.md and docs/curriculum-content-quality.md.

## Curriculum validator — 2026-11-11

Completed: reusable offline CLI, source preparation adapters, per-item evidence,
JSON/Markdown artifacts, safe normalization snapshots, mocked bounded AI review
and automated regressions. Five draft courses audited; production untouched.
External linguistic confirmation remains pending (no local reviewed dataset),
as do teacher/translator sign-off and separate publication approval.
Implementation/limits: `docs/curriculum-validator.md`; snapshot findings:
`docs/curriculum-validation-report.md`.

## Local draft preview — 2026-11-11

Completed: controlled local preview of all five unpublished A0–B2 courses using a
separate private SQLite and new reviewer, source-backed existing pages and normal
authentication. Desktop/mobile Firefox artifacts recorded; source publication and
main user DB unaffected. Primary reviewer remains at zero XP/lesson progress;
UI interaction QA used a second database. Next: pedagogical/translation review,
then separately authorized publication. Evidence: docs/curriculum-visual-review.md.

## Infrastructure finalization checkpoint — 2026-11-14

- **Completed locally:** transfer implementation/refusal/rollback tests; mandatory docs/actionlint/PostgreSQL evidence gates; ruleset import artifact and staging/recovery/security/release documentation.
- **In progress / externally blocked:** revised hosted CI, PostgreSQL cross-engine and logical/provider restore drills; no staging instance or authenticated hosting management.
- **Observed:** existing hosted full suites fail, main protected=false, Render readiness 200/database up, Netlify homepage 200/API 404.
- **Next:** owner-run PR/checks, activate protection and CI-gated hosting, validate staged routing/cookies and restore, then separately approve production cutover. A0–B2 remains draft. No automatic commit/push.

## Default npm dev curriculum — 2026-11-14

Completed: existing local SQLite backed up and populated with all five A0–B2 drafts;
all seven courses available to ordinary signed-in local users by default. Authenticated
loopback-only factory reuses existing routes/grading and preserves production filtering.
Verified: all 50 draft lessons/500 words over HTTP, idempotent rerun, original accounts,
profile XP and progress preserved; targeted tests/Ruff/mypy/frontend/docs links pass.
Remaining: pre-existing upstream preview total-count assertion and documentation contract
drift from letter_tiles remain separate fixes; editorial/production publication pending.
No commit/push or production operation performed.
