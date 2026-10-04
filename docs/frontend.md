# Frontend

> Status: **M1 implemented**. Stack: Next.js 15 (App Router) + Tailwind CSS v4 +
> TanStack Query + Framer Motion. Routes: `/`, `/learn`, `/login`.

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
│   │   ├── providers.tsx       # TanStack Query client
│   │   ├── globals.css         # Tailwind import + design tokens
│   │   ├── page.tsx            # landing + live backend status
│   │   ├── learn/page.tsx      # profile (API) + placeholder lessons
│   │   └── login/page.tsx      # UI scaffold, no auth yet
│   ├── components/
│   │   ├── app-shell.tsx       # header/nav/footer
│   │   ├── backend-status.tsx  # live GET /health indicator
│   │   ├── fade-in.tsx         # reduced-motion-aware entrance animation
│   │   └── ui/                 # button, card, badge primitives
│   ├── config/nav.ts
│   └── lib/api/
│       ├── client.ts           # typed fetch wrapper + ApiError
│       ├── client.spec.ts      # Vitest unit tests
│       ├── health.ts
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
  `/users/me`.
- **State**: server state in TanStack Query; local UI state in React. No global
  store until a concrete need appears.
- **Auth session**: not implemented. The login form is a scaffold and
  deliberately does not fake a session. When auth lands, the access token stays
  in memory and refresh uses an httpOnly cookie.

## 4. API client

`src/lib/api/client.ts` is the only place that calls `fetch`. It:

- reads the base URL from `NEXT_PUBLIC_API_URL` (default
  `http://localhost:3001/api/v1`);
- returns parsed JSON on success;
- normalises failures into `ApiError { status, code }`:
  `NETWORK_ERROR` (status `0`) when the backend is unreachable,
  the backend error `code` for HTTP errors, and `INVALID_RESPONSE` for a
  non-JSON body.

Endpoint functions (`getHealth`, `getCurrentUser`) and query hooks use this
client. Components never call `fetch` directly.

## 5. Design system

Tailwind v4 tokens are defined once in `src/app/globals.css` under `@theme`
(color palette, font) matching `design/`. UI primitives live in
`src/components/ui`. Feature components must not introduce raw hex values.

Visual concept: premium dark, purple/violet with blue/cyan accents, subtle
gradients, rounded cards, clean typography, restrained glassmorphism, responsive
desktop + mobile.

## 6. Accessibility

- Focus is always visible (global `:focus-visible` ring).
- Form controls are labelled; the login notice uses `role="status"`.
- `FadeIn` respects `prefers-reduced-motion`.
- Layout works from small mobile widths up.

## 7. Testing

Unit tests with **Vitest** for non-visual logic — currently the API client
(success, HTTP error with backend code, network error, invalid response).
Playwright end-to-end tests are planned.

## 8. Conventions

- One component per file; PascalCase filenames.
- Server components by default; `"use client"` only when needed.
- No business logic in components; call the API client.
- Styling via Tailwind utility/token classes; inline styles only for dynamic
  values that cannot be expressed as a class (e.g. a progress width).

See `plans/frontend-plan.md` for the implementation order.
