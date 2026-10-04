# Frontend

> Status: **design** (pre-implementation). Stack: Next.js (App Router) +
> Tailwind CSS + TanStack Query + Framer Motion.

## 1. Responsibilities

The frontend renders the product, manages navigation and local UI state, and
communicates with the backend over REST. It contains **no business rules** and
never talks to AI providers or the database directly.

## 2. Project structure (planned)

```
frontend/
├── src/
│   ├── app/                    # App Router routes
│   │   ├── (marketing)/        # public landing
│   │   ├── (auth)/             # login, register, reset
│   │   └── (app)/              # authenticated application shell
│   │       ├── dashboard/
│   │       ├── learn/
│   │       ├── lessons/
│   │       ├── vocabulary/
│   │       ├── practice/
│   │       ├── grammar/
│   │       ├── challenges/
│   │       ├── progress/
│   │       ├── profile/
│   │       ├── ai-tutor/
│   │       └── settings/
│   ├── components/
│   │   ├── ui/                 # design-system primitives
│   │   └── ...                 # feature components, colocated by domain
│   ├── lib/
│   │   ├── api/                # typed API client + query hooks
│   │   ├── auth/               # session handling
│   │   └── utils/
│   ├── styles/                 # Tailwind entry, tokens
│   └── config/                 # nav config, feature flags
├── public/
└── tests/                      # Playwright specs
```

## 3. Rendering and data strategy

- **Server Components** by default; client components only where interactivity
  requires them (`"use client"`).
- **Data fetching** for authenticated app screens is client-side via TanStack
  Query (simple auth model, cache control). Public/marketing pages may be server
  rendered.
- **State**: server state in TanStack Query; URL state for filters; local UI
  state in React. A global store is added only if a concrete need appears.
- **Auth session**: access token kept in memory; refresh handled via httpOnly
  cookie through the backend. Never store secrets in `localStorage`.

## 4. API client

A single typed client wraps `fetch`, injects the access token, transparently
retries once after a refresh on `401`, and normalises the backend error envelope
into a typed `ApiError`. Query hooks live next to their domain and are the only
way components read server data.

## 5. Design system

All visual primitives (color, spacing, radius, typography, motion) come from
tokens documented in `design/` and implemented once in Tailwind configuration
and `components/ui`. No ad-hoc hex values in feature components.

Visual concept: premium dark, purple/violet with blue/cyan accents, subtle
gradients, restrained glassmorphism, responsive desktop + mobile, modern
typography, smooth animations.

## 6. Accessibility

Target WCAG 2.1 AA: keyboard navigable, visible focus, semantic landmarks,
sufficient contrast (verified in `design/colors.md`), reduced-motion support for
animations, labelled form controls.

## 7. Performance

- Route-level code splitting (App Router default).
- Optimised fonts (`next/font`) and images (`next/image`).
- Server-side caching / revalidation for public content.
- Avoid over-fetching: cursor pagination and narrow DTOs.

## 8. Testing

- **Playwright** for critical flows: auth, lesson completion, vocabulary review,
  AI tutor turn.
- Component tests only where logic (not markup) warrants them.

## 9. Conventions

- One component per file; PascalCase filenames.
- Co-locate feature components with their route when not reused.
- No business logic in components; call API hooks.
- Styling via Tailwind utilities + token classes; avoid inline styles.

See `plans/frontend-plan.md` for the implementation order.
