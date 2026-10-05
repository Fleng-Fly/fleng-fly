# Frontend

> Status: **M2 implemented**. Stack: Next.js 15 (App Router) + Tailwind CSS v4 +
> TanStack Query + Framer Motion. Routes: `/`, `/learn`, `/login`, `/register`.
> Authentication and progress are wired to the FastAPI backend.

## 1. Responsibilities

The frontend renders the product, manages navigation and local UI state, and
communicates with the backend over REST. It contains no business rules and never
talks to AI providers or the database directly.

## 2. Project structure (current)

```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx          # shell, fonts, providers, metadata
│   │   ├── providers.tsx       # TanStack Query + AuthProvider
│   │   ├── globals.css         # Tailwind import + design tokens
│   │   ├── page.tsx            # landing + live backend status
│   │   ├── learn/page.tsx      # protected: profile + progress from API
│   │   ├── login/page.tsx      # real login
│   │   └── register/page.tsx   # account creation
│   ├── components/
│   │   ├── app-shell.tsx       # header/nav/footer
│   │   ├── backend-status.tsx  # live GET /health indicator
│   │   ├── user-menu.tsx       # session-aware login/logout
│   │   ├── fade-in.tsx         # reduced-motion-aware entrance animation
│   │   └── ui/                 # button, card, badge primitives
│   ├── config/nav.ts
│   ├── lib/auth/
│   │   └── auth-context.tsx    # session state + login/register/logout
│   └── lib/api/
│       ├── client.ts           # typed fetch + tokens + 401 refresh/retry
│       ├── client.spec.ts      # Vitest unit tests
│       ├── errors.ts           # user-facing error messages
│       ├── auth.ts             # register/login/logout
│       ├── health.ts
│       ├── progress.ts
│       └── users.ts
├── next.config.ts
├── postcss.config.mjs
├── eslint.config.mjs
├── vitest.config.ts
└── tsconfig.json
```

Future screens (`(auth)`, `(app)`, lessons, vocabulary, progress, AI tutor, …)
follow the plan in `plans/frontend-plan.md`; route groups are introduced when
there is more than a couple of routes.

## 3. Rendering and data strategy

- **Server Components** by default; `"use client"` only where interaction or
  client data fetching requires it (`BackendStatus`, `/learn`, `/login`).
- **Data fetching**: TanStack Query for client screens. The `/health` query
  refetches every 15s and drives the Online/Offline badge; `/learn` queries
  `/users/me` (via the session) and `/progress/me`.
- **State**: server state in TanStack Query; local UI state in React. Session
  state lives in `AuthProvider`. No global store until a concrete need appears.
- **Auth session**: the access token is held in memory only. On load,
  `AuthProvider` calls `/users/me`; if the access token is missing/expired the
  client transparently refreshes from the HttpOnly cookie and retries. `/learn`
  redirects to `/login` when there is no session.

## 4. API client

`src/lib/api/client.ts` is the only place that calls `fetch`. It:

- reads the base URL from `NEXT_PUBLIC_API_URL` (default
  `http://localhost:3001/api/v1`);
- keeps the access token in memory and attaches `Authorization: Bearer`;
- sends `credentials: 'include'` so the refresh cookie is used;
- on `401` performs one refresh (`POST /auth/refresh`) and retries the request
  once (concurrent refreshes are de-duplicated);
- returns parsed JSON on success (and `undefined` for `204`);
- normalises failures into `ApiError { status, code, details }`:
  `NETWORK_ERROR` (status `0`) when the backend is unreachable,
  the backend error `code` for HTTP errors, and `INVALID_RESPONSE` for a
  non-JSON body.

`describeApiError` (`errors.ts`) turns those into user-facing messages for 401,
403, 422, 500, backend-unavailable and database-unavailable (503). Endpoint
functions (`getHealth`, `getCurrentUser`, `register`, `login`, `logout`,
`getMyProgress`) use this client; components never call `fetch` directly.

## 5. Design system

Tailwind v4 tokens are defined once in `src/app/globals.css` under `@theme`
(color palette, font) matching `design/`. UI primitives live in
`src/components/ui`. Feature components must not introduce raw hex values.

Visual concept: premium dark, purple/violet with blue/cyan accents, subtle
gradients, rounded cards, clean typography, restrained glassmorphism, responsive
desktop + mobile.

## 6. Accessibility

- Focus is always visible (global `:focus-visible` ring).
- Form controls are labelled; form errors use `role="alert"`.
- `FadeIn` respects `prefers-reduced-motion`.
- Layout works from small mobile widths up.

## 7. Testing

Unit tests with **Vitest** for non-visual logic — the API client (success, HTTP
error with backend code, network error, invalid response, token attachment, 401
refresh-and-retry) and the auth/progress request shapes. Playwright end-to-end
tests are planned.

## 8. Conventions

- One component per file; PascalCase filenames.
- Server components by default; `"use client"` only when needed.
- No business logic in components; call the API client.
- Styling via Tailwind utility/token classes; inline styles only for dynamic
  values that cannot be expressed as a class (e.g. a progress width).

See `plans/frontend-plan.md` for the implementation order.
