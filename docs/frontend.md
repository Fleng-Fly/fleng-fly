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
├── lesson.html         # protected: lesson theory (?slug=...)
├── settings.html       # protected: profile display
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
    ├── courses.js      # catalog list
    ├── course.js       # course detail + lesson list
    ├── lesson.js       # lesson theory (safe light-markup renderer)
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

`js/api.js` also exposes the catalog reads used by the course pages:
`listCourses()`, `getCourse(slug)` and `getLesson(slug)`.

### Course pages

`courses.html`, `course.html` and `lesson.html` load data client-side and render
it with `layout.js` helpers, always via `textContent`:

- `courses.js` lists published courses as cards (title, CEFR level, description,
  lesson count), with loading, empty and error states.
- `course.js` reads `?slug=` and shows the course header plus its ordered lesson
  list; a missing/unpublished course shows a friendly "not found" state.
- `lesson.js` reads `?slug=` and renders theory using a tiny safe renderer: blank
  lines separate blocks, `## ` is a heading, `- ` lines are a list, everything
  else is a paragraph (see `app/db/models.py`). No HTML is ever stored or
  interpreted.

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
