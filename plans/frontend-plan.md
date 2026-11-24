# Frontend Plan

- [x] Shared Test Completion Screen for Course Lessons, My Words Mixed Practice
  (including Course Words Tests), and Placement Test.
  Verification and current data limits are recorded in
  [FLENG_TEST_COMPLETION_REPORT.md](../FLENG_TEST_COMPLETION_REPORT.md).

- Completed: My Words offers Mixed Practice with balanced formats, FIFO retries,
  reload recovery, and a replayable summary. Learner review uses the existing API.
- Completed: Course Words links directly to Mixed Practice through Tests above its filters.

> Stack: plain HTML5 + CSS3 + vanilla JavaScript, served statically by FastAPI
> (same origin as `/api/v1`). No framework, no TypeScript, no build step.
> See `docs/frontend.md`.
> Legend: ✅ done · 🚧 in progress · ⬜ next. Checklist uses [x]/[~]/[ ].

## Phase A — Static delivery + auth ✅

- [x] Convert `frontend/` to static HTML/CSS/JS (no Next.js/React/TypeScript).
- [x] Serve the static files from FastAPI (`StaticFiles`); single server.
- [x] Shared layout, navigation and design tokens in `css/app.css`.
- [x] `js/api.js` API client: in-memory access token, 401 refresh-and-retry,
      de-duplicated refresh, `credentials: 'include'`, error normalisation.
- [x] `js/session.js` session restore + protected-page redirect.
- [x] Pages: landing, login, register, dashboard (profile + progress), settings.
- [x] Same-origin CSRF origin acceptance in the backend.
- [x] Root tooling runs one server (no Next.js); static-serving tests added.

## Phase B — Catalog & lessons ✅

- [x] Course catalogue page (`courses.html`) and course detail page
      (`course.html`) consuming `/courses` and `/courses/{slug}`.
- [x] Lesson page (`lesson.html`) rendering theory from `/lessons/{slug}`.
- [x] Automatic answer checking in lessons and vocabulary practice.
- [x] Exercises + submission and results view: radios / short answer /
      self-check, inline correctness, `+XP`, revealed answer and explanation, and
      a live progress summary.
- [x] Dashboard shows persisted lessons/exercises/XP and per-course progress.
- [~] Dashboard visual phase: responsive sidebar, profile menu, catalog search,
  progress ring, current course, streak and learned-word count implemented.
  Firefox checks at 360/768/desktop passed on local SQLite (2026-10-22).
  Exact Figma comparison remains pending.
  Notifications and dedicated word/topic search remain unavailable.
- [x] Dashboard redesign (2026-11-20): welcome hero with CTA, Your Progress, Quick
  Access (Lessons/Words/Progress/Leaderboard), Current Course, Daily Goals,
  next-course/placement cards and a benefits strip; EN/UK; real data only. No
  notifications or Authors page exist, so neither is shown.
  Leaderboard is implemented (see 2026-11-04 update).
- [x] Lessons visual phase: shared Dashboard workspace, lesson hero and four
  keyboard-accessible tabs, three existing exercise types, server feedback,
  Test navigation/preview, lesson-filtered saved vocabulary and responsive
  360/768/desktop layout. Firefox local smoke passed (2026-10-22).
  Exact Figma comparison remains pending; custom test generation, timer and
  unimplemented exercise types are intentionally unavailable.

- [x] Practice and Test advance after grading and revisit unfinished attempts
  after the unseen questions. Letter tiles support drag and drop, tap and keyboard.

## Phase C — Progress & profile ⬜

- [x] Dashboard progress summary and current-course view.
- [ ] Standalone Progress screen and per-skill/activity views.
- [x] Settings profile/email form, language preference, password change and logout.

## Phase D — AI tutor ⬜

- [ ] "Ask the tutor" panel with structured lesson/question context.
- [ ] Error/loading states; AI failure never blocks the lesson.

## Later sections ⬜

- [ ] Vocabulary, practice, challenges, gamification surfaces.
- [ ] Browser e2e suite and full accessibility audit.

## Visual direction

Premium dark, purple/violet + blue/cyan accents, subtle gradients, rounded
cards, responsive layouts. Tokens live in `frontend/css/app.css` and align with
`design/`; no ad-hoc colors.

## Risks / watch-items

- Keep the API client the single HTTP chokepoint (`js/api.js`).
- Render untrusted text with `textContent`, never `innerHTML`.
- Avoid reintroducing a framework or build step; keep pages small.

- [x] Integrate `CSS.star4life` gradients and auth cards into the existing API-connected static pages, with valid CSS and responsive sizing.


## Leaderboard + hosting preparation — 2026-11-04

- **Completed:** authenticated all-time XP ranking, top-3 cards, learner table,
  own rank, short/empty/loading/error/retry states and responsive styles.
- **Completed:** production launcher/Procfile, environment template, secure-cookie
  and secret guards, exact HTTPS CORS origins, DB readiness and deployment notes.
- **Next:** choose hosting/managed PostgreSQL and supply production secrets;
  apply migrations and verify public HTTPS auth, proxy trust and optional AI.
- **Not verified:** exact Figma comparison (source not supplied), browser layout
  at 360/768/desktop (browser unavailable), live hosting/PostgreSQL/OpenRouter/SMTP.

## Courses Catalog + Course Details — 2026-11-04

- **Completed:** existing workspace/sidebar/header/mobile drawer reused; Courses
  selected; compact purple catalog and course hero/lesson rows implemented.
- **Completed:** dynamic published courses/lessons, joint title/description search
  and CEFR filter, clear/reset, real aggregate/individual progress, Start/Continue/
  Review links, completed/empty/error/retry/session states and return refresh.
- **Completed:** reduced-motion/responsive CSS, six DOM regression scenarios,
  full pytest (184 passed / 15 skipped), Ruff, mypy, syntax/whitespace checks,
  local dev-server and API smoke; independent self-review and docs/map updates.
- **Blocked:** exact Stitch comparison; linked project inaccessible, local export
  not identified and no screenshots attached. Browser inventory is empty.
- **Next:** browser visual/interaction QA at 360/768/1440px, compare accessible
  final Stitch screens, verify shared navigation and AI in browser.
- **Commits:** not created, per task instruction. See `docs/courses-implementation.md`.

## Website release — 2026-11-16

Implemented latest purple interface, personal vocabulary and
four animated practice modes/results; removed install UI/standalone metadata.
Main's A0 filter and three lesson tabs preserved. Assets revalidate; footer/sidebar
show Web 2026.11.16. External publishing and live authenticated QA remain pending.


## Progress analytics UI — 2026-11-16

- Completed: isolated feat/progress-ui worktree based on analytics 99879f3;
  Progress page using real totals, active courses, completion and current/best streak.
- Completed: null XP-history explanation, loading/empty/error/retry, safe rendering
  and session lifecycle; frontend regressions and Firefox at 1440/768/390/360 px.
- Next: integrate the branch with the separately maintained workspace navigation
  if a global Progress entry is desired; shared files remain untouched here.
- No backend changes, commit, push or merge. Evidence: docs/frontend.md.

## Words and compact AI — 2026-11-16

- Implemented: unified Words disclosure and existing personal practice preserved;
  Course Words frontend connected to existing catalog/vocabulary APIs.
- Implemented: compact purple assistant, safe DOM Markdown, live character count,
  typing, options-menu history refresh and manual-scroll preservation.
- Verification in progress: frontend regressions and Firefox responsive/keyboard
  review. No backend AI/limit/schema changes; no commit/push.
- Screenshot references were not attached to the received task; visual choices
  follow the written brief and existing Fleng theme. Exact comparison is pending.

Verification complete: all seven frontend test files pass; Markdown/Words eight
checks and widget eleven checks pass; legacy PWA cleanup passes. Firefox checked
1440/768/390/360px, real temporary catalog/save, mocked SSE, manual scroll and
simulated keyboard/reduced height. No horizontal overflow after the scrollbar
width correction. Native disclosure focus/click verified; headless system-key
activation, physical mobile keyboards and missing screenshot comparison remain
unverified. Self-review covered DOM-only rendering/URL policy, request races,
existing practice/stream lifecycle and scoped styles. Details:
`docs/words-ai-interface.md`. No commit/push.

## UX development sprint

- [x] Remove Our Team assets/navigation and obsolete journey coverage.
- [x] Clarify public landing, registration CTA and remove operational status UI.
- [x] Existing Placement onboarding and Dashboard recommendations.
- [ ] Exercise guidance, feedback and navigation.
- [ ] EN/UK shared localization and mobile/accessibility polish.

## UX overhaul (feat/ux-overhaul) 🚧

- [x] Removed the Our Team page, navigation links, styles and tests.
- [x] Landing page: clear start flow, registration as the primary action, no public
      backend/SQLite status.
- [x] EN/UK i18n (single HTML set, dictionaries, saved choice, `preferred_language` sync).
- [x] Dashboard: Continue learning, real placement next step, compact progress.
- [x] Lesson player: per-type instructions, clearer results, completion screen with next
      lesson/course; removed developer-only template panels.
- [x] Catalog: CEFR level, progress, Start/Continue/Review, placement-based
      "Recommended" badge, next-course banner on completed courses.
- [x] Translated: header, workspace, auth, dashboard, catalog, lesson, settings,
      leaderboard, progress, vocabulary, course words, placement test UI.
- [ ] Translate the AI assistant widget.
- [x] Hints, EN/UK explanations, wrong-answer notes and lesson Explanation block for A0–A1
      (draft content, served outside production until reviewed; `docs/exercise-guidance.md`).
- [ ] Guidance content for A2–B2 and teacher/translator review of A0–A1.
- [ ] Translatable placement text.
- [ ] Real-browser checks at 1440/768/390/360 px (no browser was available).
