# Courses implementation — 2026-11-04

## Scope and design source

Courses Catalog and Course Details now use the shared application workspace and
existing FastAPI APIs. No backend/schema/auth/grading changes or dependencies.
No commits or push, following the task's explicit instruction.

Stitch project `15554211763647916426` was inaccessible through the available web
tool. No local export was identified and no screenshots were attached to the
request. The implementation follows the supplied simplified screen description
and existing Fleng design tokens. Exact final Stitch fidelity is NOT VERIFIED.
The computer-use inventory returned no available apps/browsers, so visual and
interactive browser verification, including 360/768/1440px, is NOT VERIFIED.
Responsive rules are implemented; this does not claim rendered layout coverage.

## Files

- `frontend/courses.html`, `frontend/course.html`: workspace page markup.
- `frontend/js/courses.js`: catalog, joint search/filter, API course progress.
- `frontend/js/course.js`: dynamic hero, individual lesson states/actions.
- `frontend/js/catalog-ui.js`: shared progress and state rendering.
- `frontend/css/courses.css`: scoped responsive treatment and animations.
- `frontend/js/workspace.js`: Courses selection/label for these pages only.
- `scripts/test-courses.mjs`: DOM regression checks without new dependencies.
- `scripts/backend-stabilization-smoke.py`: course assets, real API reads,
  slug context and read-only progress checks in an isolated database.
- `docs/frontend.md`, `project-map/modules.md`, `project-map/data-flow.md`,
  `plans/frontend-plan.md`: current behavior, ownership, flow and remaining QA.

## Verification

- Full pytest: **184 passed, 15 skipped**, one existing Starlette/httpx
  deprecation warning. PostgreSQL cases skip without the test database.
- Ruff: passed. mypy: passed, 64 source files.
- JavaScript syntax checks: passed. `git diff --check`: passed.
- `node --experimental-vm-modules scripts/test-courses.mjs`: **6 passed**.
  Exercises title/description search, CEFR intersection, clear/reset,
  Start/Continue/Review, course completion, history refresh, routes, empty/error/
  retry states, missing courses, absent lessons and session redirects.
  Uses a minimal DOM harness; it does not verify CSS, mobile drawers or browser
  rendering. Node emits the expected experimental VM-module warning.
- `npm run dev`: started successfully with the existing local SQLite catalog;
  HTTP health returned database up and Courses API returned English Foundations
  (A1, 3 lessons) and Everyday Conversations (B1, 3 lessons).
- Dev-server smoke uses a temporary SQLite database, real authentication,
  course/lesson APIs, once-only XP, persistence, production launcher and origin
  guards. Reading individual lesson progress is checked not to change aggregate
  progress. Catalog and course detail assets are requested over real HTTP.
- In sandbox, SQLite preparation/tests stalled, as already documented in
  `docs/testing.md`; rerunning outside sandbox completed successfully.

## Independent self-review

Reviewed API contracts against catalog/progress/exercise schemas; confirmed
published-only backend reads, safe textContent rendering, no invented progress,
no client XP mutation, stable slug routes, session failure distinction, retry,
zero-total guard, scoped CSS and reduced motion. Rechecked that workspace's new
branch leaves existing Dashboard/Leaderboard/Lessons behavior intact. The player
already restores course context from the server and needs no grading changes.

## Next

Provide accessible final Stitch screens/export and complete visual comparison;
run browser scenarios at 360/768/1440px, mobile drawer/profile controls, actual
Start/Continue/Review clicks and back/forward restoration. Shared AI remains
unchanged but its browser regression is also unverified. Changes are prepared
for review and a separate user-created Git commit.
