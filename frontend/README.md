# frontend/

Static user interface of Fleng: **plain HTML, CSS and vanilla JavaScript**, with
no framework and no build step. FastAPI serves these files from the same origin
as the API (`/api/v1`).

## Stack

- HTML5, CSS3 and browser JavaScript (ES modules).
- `fetch` for HTTP.
- No React/Next.js/Vue/Angular, no TypeScript, no bundler, no UI library.

## Layout

```
frontend/
├── index.html          # landing
├── login.html          # sign in
├── register.html       # create account
├── dashboard.html      # protected: profile + progress
├── courses.html        # protected: course catalog
├── course.html         # protected: course detail (?slug=...)
├── lesson.html         # protected: lesson theory (?slug=...)
├── settings.html       # protected: profile display
├── css/app.css         # design tokens + shared styles
└── js/
    ├── api.js          # fetch wrapper, in-memory access token, refresh-on-401
    ├── errors.js       # user-facing error messages
    ├── session.js      # loadSession / requireSession guard
    ├── layout.js       # shared header, backend-status badge, DOM helpers
    ├── home.js
    ├── login.js
    ├── register.js
    ├── dashboard.js
    ├── courses.js      # catalog list
    ├── course.js       # course detail + lesson list
    ├── lesson.js       # lesson theory (safe markup renderer)
    └── settings.js
```

## Conventions

- `.html` links are explicit (`/login.html`); the static server does not rewrite
  `/login` to `login.html`.
- All user-controlled or server-provided text is rendered with `textContent`,
  never `innerHTML`.
- The access token lives in a JavaScript variable only (never
  `localStorage`/`sessionStorage`); the refresh token stays in the HttpOnly
  cookie. Protected pages call `requireSession()` and redirect to `login.html`
  when there is no session.
- The API base URL is the relative `/api/v1`, so there is no environment
  configuration and the frontend is same-origin with the API.

## Where to look

- Serving/architecture: `docs/frontend.md`, `project-map/architecture.md`
- Design tokens: `design/colors.md`, `design/typography.md`
- Pages/UX: `design/pages.md`, `design/ux-flow.md`
