# API Plan

> Aligns with `plans/roadmap.md`. Contracts and map: `docs/api.md`.
> Implementation follows the backend stages in `plans/backend-plan.md`.

## Approach

- Versioned REST at `/api/v1`; additive changes within a version.
- Each endpoint lands with: Pydantic schema validation, ownership/role checks,
  the standard error envelope, rate-limit decision, and API e2e tests.
- Document every endpoint in `docs/api.md` and summarise in
  `project-map/api-map.md` in the same commit.

## Stage 1 — Auth & users

- [x] `POST /auth/register`, `/login`, `/refresh`, `/logout`
- [x] `GET /users/me` (read-only, bearer)
- [x] `GET /health`
- [ ] `POST /auth/verify-email`, `/forgot-password`, `/reset-password`
- [ ] `GET /auth/me` (superseded by `GET /users/me`)
- [ ] `PATCH /users/me`, `/users/me/settings`, `DELETE /users/me`
- [ ] `GET /users/:id` (limited public profile)

## Stage 2 — Learning

- [ ] `GET /courses`, `/courses/:idOrSlug`; admin `POST/PATCH/DELETE`
- [ ] `GET /lessons/:idOrSlug`, `POST /lessons/:id/start`, `/complete`,
      `GET /lessons/:id/progress`
- [ ] `GET /exercises/:id`, `POST /exercises/:id/submit`, `GET /exercises/submissions`

## Stage 3 — Vocabulary & progress

- [ ] `GET /vocabulary/words`, `GET/POST/PATCH/DELETE /vocabulary/me`
- [ ] `GET /vocabulary/reviews/due`, `POST /vocabulary/reviews`
- [x] `GET /progress/me` (own aggregate progress)
- [ ] `GET /progress/summary`, `/progress/courses/:courseId`, `/progress/skills`,
      `/progress/activity`
- [ ] Progress write endpoints, recorded server-side on lesson completion

## Stage 4 — AI, challenges, notifications

- [ ] `GET/POST /ai/conversations`, `GET /ai/conversations/:id`,
      `POST /ai/conversations/:id/messages`
- [ ] `POST /ai/writing/correct`, `POST /ai/grammar/explain`,
      `GET /ai/recommendations`
- [ ] `GET /challenges`, `/challenges/:id`, `POST /challenges/:id/join`,
      `GET /challenges/:id/leaderboard`
- [ ] `GET /notifications`, `POST /notifications/:id/read`, `/read-all`

## Cross-cutting

- [ ] Shared pagination/filter Pydantic schemas.
- [ ] Consistent error codes registry (single source).
- [ ] OpenAPI generation once the surface stabilises (optional; not a priority).
- [ ] Rate-limit policy per endpoint class (`docs/security.md §9`).

## Risks / watch-items

- Contract drift between docs and code — update docs in the same commit.
- Avoid resource explosion: group related reads (dashboard summary vs. many calls).
- Versioning: introduce `/v2` only for breaking changes, with a migration note.
