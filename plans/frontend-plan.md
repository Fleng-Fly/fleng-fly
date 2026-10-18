# Frontend Plan

> Stack: plain HTML5 + CSS3 + vanilla JavaScript, served statically by FastAPI
> (same origin as `/api/v1`). No framework, no TypeScript, no build step.
> See `docs/frontend.md`.
> Legend: ✅ done · 🚧 in progress · ⬜ next.

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

## Phase B — Catalog & lessons 🚧

- [x] Course catalogue page (`courses.html`) and course detail page
      (`course.html`) consuming `/courses` and `/courses/{slug}`.
- [x] Lesson page (`lesson.html`) rendering theory from `/lessons/{slug}`.
- [ ] Exercises + quiz submission and results view (needs the exercises API).

## Phase C — Progress & profile ⬜

- [ ] Progress summary / per-course views.
- [ ] Profile editing (settings form) once `PATCH /users/me` exists.

## Phase D — AI tutor ⬜

- [ ] "Ask the tutor" panel with structured lesson/question context.
- [ ] Error/loading states; AI failure never blocks the lesson.

## Later sections ⬜

- [ ] Vocabulary, practice, challenges, gamification surfaces.
- [ ] Browser e2e (Playwright) and accessibility pass.

## Visual direction

Premium dark, purple/violet + blue/cyan accents, subtle gradients, rounded
cards, responsive layouts. Tokens live in `frontend/css/app.css` and align with
`design/`; no ad-hoc colors.

## Risks / watch-items

- Keep the API client the single HTTP chokepoint (`js/api.js`).
- Render untrusted text with `textContent`, never `innerHTML`.
- Avoid reintroducing a framework or build step; keep pages small.


- [x] Integrate `CSS.star4life` gradients and auth cards into the existing API-connected static pages, with valid CSS and responsive sizing.
