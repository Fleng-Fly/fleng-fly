# Frontend

> Status: **M2 implemented (Phase A)**. Stack: plain HTML5 / CSS3 / vanilla
> JavaScript. The static files are served by the FastAPI backend from the same
> origin as `/api/v1`. Routes: `/index.html`, `/login.html`, `/register.html`,
> `/dashboard.html`, `/settings.html`.

## 1. Responsibilities

The frontend renders the product, manages navigation and local UI state, and
communicates with the backend over REST. It contains no business rules, never
talks to the database or AI providers, and holds no secrets.

## 2. Delivery model

There is **no frontend build step and no separate frontend server**. The pages,
styles and scripts live in `frontend/` and are mounted by the backend
(`backend/app/main.py`) with Starlette's `StaticFiles(html=True)` at `/`, after
the `/api/v1` router. The frontend therefore runs on the same origin as the API,
which keeps the HttpOnly refresh cookie first-party and removes the need for CORS
in the browser.

Consequences:

- Page links are explicit (`/login.html`); the static server does not rewrite
  `/login` to `login.html`.
- JavaScript is loaded as ES modules (`<script type="module">`), which requires
  the `text/javascript` MIME type that `StaticFiles` provides.
- The API base URL is the relative `/api/v1`, so there is no environment
  configuration in the frontend.
- `frontend_dir` in `Settings` overrides the served directory; by default the
  repository `frontend/` directory is used.

## 3. Project structure

```
frontend/
├── index.html          # landing (hero, features, live backend status)
├── login.html          # sign in
├── register.html       # create account
├── dashboard.html      # protected: profile + progress from the API
├── courses.html        # protected: course catalog
├── course.html         # protected: course detail + lesson list (?slug=...)
├── lesson.html         # protected: lesson player (?slug=...)
├── settings.html       # protected: account settings
├── css/app.css         # design tokens + shared styles
└── js/
    ├── api.js          # fetch wrapper + endpoint helpers
    ├── errors.js       # describeApiError
    ├── session.js      # loadSession / requireSession
    ├── layout.js       # shared header, backend-status badge, DOM helpers
    ├── home.js
    ├── login.js
    ├── register.js
    ├── dashboard.js
    ├── workspace.js    # Dashboard/Lessons sidebar, header, search and profile menu
    ├── courses.js      # catalog list
    ├── course.js       # course detail + lesson list
    ├── lesson.js       # theory + exercises + submissions + progress
    └── settings.js
```

## 4. API client and session

`js/api.js` is the only place that calls `fetch`. It mirrors the previous typed
client:

- keeps the access token in a module variable (memory only, never
  `localStorage`/`sessionStorage`);
- sends `credentials: 'include'` so the HttpOnly refresh cookie is sent;
- attaches `Authorization: Bearer` when a token is present;
- on a `401` performs at most one refresh (`POST /auth/refresh`) and retries the
  request once; concurrent refreshes are de-duplicated;
- returns parsed JSON on success (and `undefined` for `204`);
- normalises failures into `ApiError { status, code, details }`:
  `NETWORK_ERROR` (status `0`), the backend error `code`, and
  `INVALID_RESPONSE` for a non-JSON body.

`js/session.js`:

- `loadSession()` calls `GET /users/me`, which transparently refreshes the
  access token from the refresh cookie, and returns the user or `null`.
- `requireSession()` is used by protected pages; it redirects to `login.html`
  when there is no session.

`js/errors.js` turns errors into user-facing messages for 401, 403, 404, 422,
503, network failure and the default case.

`js/api.js` also exposes the catalog reads and lesson flow used by the course
pages: `listCourses()`, `getCourse(slug)`, `getLesson(slug)`,
`startLesson(slug)`, `getLessonProgress(slug)`, `submitAnswer(slug, payload)`
and `getLessonVocabulary(lessonId, offset, limit)`.

### Course pages

`courses.html`, `course.html` and `lesson.html` load data client-side and render
it with `layout.js` helpers, always via `textContent`:

- `courses.js` lists published courses as cards (title, CEFR level, description,
  lesson count), with loading, empty and error states.
- `course.js` reads `?slug=` and shows the course header plus its ordered lesson
  list; a missing/unpublished course shows a friendly "not found" state.
- `lesson.js` loads the published lesson and the caller's lesson progress, then
  starts the lesson only if it has not begun. Theory uses the existing safe text
  renderer. Theory is the default; Practice shows exercises one at a time with
  Previous/Next and a current-lesson preview. Valid tab query parameters select
  Practice/Vocabulary; obsolete Test links fall back to Theory. Practice retains
  the same server submissions and progress. Radios (`single_choice`), short answers (`text`),
  and self-assessment (`self_check`) are supported. The Vocabulary tab loads
  only the caller's saved words filtered by this lesson ID; it shows an honest
  empty state when there are none. Last submitted answers are restored from
  `GET /lessons/{slug}/progress`; unsent drafts exist only in page memory.
  Answer keys remain available only in the submission response. XP and
  completion are computed by the backend. The custom template builder is
  disabled because it has no API; “Use template” opens Practice.
  All server text is inserted with `textContent`.

`dashboard.html` and `lesson.html` use `js/workspace.js` for their sidebar and topbar. The mobile sidebar
opens as a keyboard-accessible drawer; the profile menu links to Settings and
uses the existing logout API. The topbar searches published course titles,
descriptions, levels and lesson titles/summaries through the existing catalog
API. Dedicated word/topic search and notifications remain unavailable.
Leaderboard now uses the same workspace (see 2026-11-04 update).

`dashboard.js` renders `GET /users/me`, `GET /progress/me`,
`GET /streaks/me` and `GET /vocabulary/stats`. The ring is completed published
lessons divided by all published lessons; no denominator displays an unavailable
state. Study time is the sum of estimated minutes of completed lessons. The
current course is an unfinished started course with the highest completion
ratio; catalog order breaks ties. If no unfinished course remains, a completed
course is shown for review. A course with no started lessons is never labelled
current. `frontend/css/dashboard.css` contains the scoped visual treatment and
respects reduced motion. No local progress cache is used.

`js/layout.js` renders the shared header (brand, nav, session-aware
login/logout), the live backend-status badge from `GET /health` (polled every
15s), and a small `el()` DOM helper.

## 5. Design system

Design tokens from `design/colors.md` and `design/typography.md` live in
`:root` in `css/app.css` (dark `ink-*` palette, violet/cyan accents, semantic
colors, radius, focus ring). Shared patterns: `.card`, `.btn`, `.field`,
`.alert`, `.badge`, `.stat`, `.definition`. Components must not introduce raw
hex values when a token exists.

Visual concept: premium dark, purple/violet with blue/cyan accents, subtle
gradients, rounded cards, clean typography, responsive desktop + mobile.

## 6. Accessibility

- Focus is always visible (global `:focus-visible` ring).
- Form controls are labelled; form errors use `role="alert"`.
- Forms use native validation (`required`, `type="email"`, `minlength`).
- Layout works from small mobile widths up.

## 7. Security rules for the frontend

- Render all user-controlled or server-provided text with `textContent`, never
  `innerHTML`.
- Never store tokens in `localStorage`/`sessionStorage`; the access token is
  memory-only and the refresh token is an HttpOnly cookie.
- No secrets, keys or provider credentials in frontend files.
- No `fetch` calls outside `js/api.js`.

## 8. Testing

There is no frontend test framework (no build system). Behaviour is covered by:

- backend tests that serve the static files over ASGI
  (`backend/tests/test_frontend.py`) and exercise the auth/progress API
  (`test_auth.py`, `test_users.py`, `test_progress.py`);
- manual/browser verification of the critical journey (register → login →
  dashboard → reload → logout).

Browser end-to-end tests (Playwright) remain planned.

## 9. Conventions

- One page per HTML file; one script per page; shared logic in `js/`.
- JavaScript is straightforward ES modules; no abstractions without a clear need.
- Keep `js/api.js` the single HTTP chokepoint.
- Update `design/` and this document when the visual language changes.

The styles from `CSS.star4life/CSS/` are adapted in `frontend/css/star4life.css`, loaded after `app.css` on every page. Login and registration use the `log-in` and `sign-up` body classes. Invalid reference syntax, fixed desktop dimensions and the missing font dependency are omitted; existing API forms and responsive layouts are preserved.


### Floating Fleng AI — 2026-11-01

Authenticated Dashboard and Lessons reuse `js/ai-assistant.js`, `js/ai-stream.js`
and `css/ai-assistant.css`. The component calls the existing authenticated AI API,
restores owned conversations and renders streaming/plain text safely. Lessons
provides a callback for current lesson/exercise IDs; backend owns context loading.
Close/minimize retains the in-flight response on-page. Navigation disconnects it.
Responsive/keyboard behavior is implemented but browser/device QA remains pending.
See [AI integration](ai-assistant-integration.md).


## Leaderboard — 2026-11-04

`/leaderboard.html` shares Dashboard/Lessons workspace chrome. The authenticated
`GET /leaderboard` response drives top-3 cards and the ranked table; caller rows
are highlighted and an out-of-top-100 position stays visible. All names use
textContent. Cards stack below 540px; the semantic table has a keyboard-focusable
horizontal scroll region. Loading, empty and retryable error states include
session-unavailable handling. Browser/Figma visual comparison remains unverified.

## Courses Catalog and Course Details — 2026-11-04

Both course pages now mount the existing workspace sidebar/topbar, profile menu,
global search and mobile drawer. `mountWorkspace('courses')` selects the Courses
entry; Dashboard/Leaderboard layouts and lesson grading remain unchanged.
`css/courses.css` scopes the two-column catalog, single-column mobile layout,
compact lesson rows, purple tokens, focus/hover states and reduced-motion rules.
`js/catalog-ui.js` shares progress bars and loading/empty/error messages.

- Catalog reads `GET /courses` and `GET /progress/me`. Search matches title and
  description without case sensitivity and combines with All/A1/A2/B1/B2 CEFR
  filters locally. Clear removes only the query; Reset filters removes both.
- Course details read `GET /courses/{slug}`, `/progress/me` and existing
  `GET /lessons/{slug}/progress` for each published lesson. Per-lesson reads are
  needed because the aggregate endpoint does not expose individual statuses.
- Completion percentage is rounded `lessonsCompleted / lessonsTotal * 100`
  (zero for an empty course). Start/Continue/Review uses server counts;
  lesson actions use `completed` and `startedAt`. No local progress storage,
  start requests or XP writes occur on either course page. Unavailable progress
  produces an error rather than fabricated zero progress.
- Catalog actions open `/course.html?slug=...`; lesson actions open the existing
  `/lesson.html?slug=...`. The lesson response already supplies `courseSlug`
  for its breadcrumb and completion link. Course Details has Back to Courses.
- Initial navigation, cached history restoration, window focus and returning
  from a hidden tab reload current data; concurrent loads are de-duplicated.
  Missing/unpublished content, no lessons, empty/no-match catalog, API errors,
  retry, unavailable session services and expired sessions are handled.
- AI remains attached explicitly by Dashboard/Lessons, not automatically by
  workspace. Course pages do not create another assistant or change AI APIs.

Verification and source limitations: [course implementation report](courses-implementation.md).

## Global assistant — 2026-11-04

Supersedes the page-specific AI mounting described above: every authenticated
`setWorkspaceUser()` now mounts the singleton assistant, including Courses,
Course Details, Leaderboard and Settings. Dashboard/Lessons share that path;
Lessons supplies context with `setWorkspaceAIContext()`. Logout/account change
clears private UI, aborts generation and removes the selection for that user;
ordinary navigation preserves the selection and restores owned backend history.
Cached-document restoration verifies the session first. Public pages stay unchanged.
See [AI security audit](ai-security-audit.md) for checks and deployment limits.
