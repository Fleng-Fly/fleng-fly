# Milestones & Status

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
| M5 | Vocabulary + SRS | ⬜ | words, user vocabulary, flashcards |
| M6 | Gamification | ⬜ | XP, levels, streaks, achievements |
| M7 | Frontend MVP | ⬜ | app shell + core screens + design system |
| M8 | AI tutor | ⬜ | Python AI layer + tutor + writing correction |
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
| M4 | `single_choice`/`text` complete on a correct answer; `self_check` completes on attempt | The server cannot objectively grade free text; self-check is explicitly self-assessed |
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
