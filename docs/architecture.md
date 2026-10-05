# Architecture

> Status: **M2 implemented** — the frontend↔backend↔database foundation plus
> authentication and progress (`/auth/*`, `/users/me`, `/progress/me`). The
> learning catalog and AI are design-only. This document is the canonical
> description of how Fleng is built; update it when the real architecture
> diverges.

## 1. Goals and constraints

- A web platform for learning English with structured content, interactive
  practice, gamified progress and AI assistance.
- Built and maintained by several agents/developers → strong conventions,
  explicit boundaries, small commits.
- Start simple and extensible. **No premature microservices.**
- TypeScript on the frontend, Python on the backend — each where it fits best.

Non-goals for the MVP:

- Native mobile apps, real-time multiplayer, or a custom ML training stack.
- Multi-region deployment, sharding, or event streaming.

## 2. Architectural style

**Modular monolith.**

- **Frontend** (Next.js / TypeScript) is a single deployable that renders the
  product and talks to the backend over HTTP/JSON.
- **Backend** (FastAPI / Python) is a single deployable, internally split into
  modules with explicit dependencies. FastAPI is the **only** backend framework:
  there is no NestJS/Express/Node.js or TypeScript code in `backend/`.
- **AI layer** is a Python package consumed by the backend. It isolates
  provider-specific code and prompt/response handling. It is *not* a service.
- **PostgreSQL** is the single source of persistent truth, accessed only through
  SQLAlchemy (async) from the backend; schema changes go through Alembic.

```
Browser
  │
  ▼
┌──────────────────────────┐
│ Frontend — Next.js       │  UI, routing, client state, server-state cache
└─────────────┬────────────┘
              │ HTTPS · REST /api/v1
              ▼
┌──────────────────────────────────────────────────────────┐
│ Backend — FastAPI (modular monolith)                     │
│                                                          │
│  Cross-cutting: dependencies · validation · logging      │
│                 error handlers · rate limiting           │
│                                                          │
│  ┌────────┐ ┌────────┐ ┌──────────┐ ┌─────────────┐      │
│  │ auth   │ │ users  │ │ catalog  │ │ content     │      │
│  └────────┘ └────────┘ └──────────┘ └─────────────┘      │
│  ┌────────────┐ ┌────────────┐ ┌──────────────┐          │
│  │ exercises  │ │ vocabulary │ │ progress     │          │
│  └────────────┘ └────────────┘ └──────────────┘          │
│  ┌──────────────┐ ┌────────────┐ ┌──────────────┐        │
│  │ gamification │ │ challenges │ │ recommend.   │        │
│  └──────────────┘ └────────────┘ └──────────────┘        │
│  ┌────────┐ ┌───────────────┐ ┌───────────┐              │
│  │ ai     │ │ notifications │ │ analytics │              │
│  └───┬────┘ └───────────────┘ └───────────┘              │
└──────┼───────────────────────────────────────────────────┘
       │ imports (in-process, Python)
       ▼
┌──────────────────────────┐
│ AI layer                 │  providers · prompts · parsing · guardrails
└─────────────┬────────────┘
              │ HTTPS
              ▼
      External AI providers

              ▲
              │ SQLAlchemy (async) → asyncpg
┌──────────────────────────┐
│ PostgreSQL               │
└──────────────────────────┘
```

## 3. Layer responsibilities

| Layer    | Owns                                                        | Must not |
| -------- | ----------------------------------------------------------- | -------- |
| Frontend | Rendering, routing, forms, client cache, design system      | Contain business rules, call AI providers directly, store secrets |
| Backend  | Business rules, validation, authz, persistence, orchestration | Contain UI concerns, expose provider-specific AI payloads |
| AI layer | Provider clients, prompts, response parsing, guardrails      | Know about HTTP, FastAPI, SQLAlchemy, or the database |
| Database | Data integrity, constraints, indexes                         | Be bypassed by ad-hoc SQL outside migrations |

## 4. Backend module boundaries

Each module owns its data and exposes a service. Rules:

1. A module may import another module's **service**, never reach into its
   internals.
2. Routers do HTTP + auth + validation only; no business logic.
3. Persistence lives in services (or thin repositories); complex queries may
   live in a dedicated query function inside the module.
4. Cross-cutting concerns (auth, logging, validation, errors, rate limits) are
   implemented once as dependencies/handlers, not per-module copies.

Modules, responsibilities and dependencies: `project-map/modules.md`.

## 5. Data flow (representative)

### 5.1 Health check

```
GET /api/v1/health
  → HealthResponse: `SELECT 1` (database up/down), never fails while the API is up
```

### 5.2 Authentication and progress (implemented)

```
POST /api/v1/auth/register | /login
  → auth module validates input, hashes/verifies the password (argon2id)
  → issues a short-lived access JWT + an opaque refresh token
  → refresh token stored hashed; raw value set in an HttpOnly cookie
  → response: { accessToken, user }

Authenticated request
  → Authorization: Bearer <access>
  → get_current_user verifies the JWT and loads the User (+ Profile)
  → GET /users/me returns the profile; GET /progress/me returns progress

POST /api/v1/auth/refresh
  → validate the cookie token, rotate it (revoke old, issue new)
  → replay of a revoked token revokes the whole session set (reuse detection)
  → response: { accessToken } + rotated cookie
```

### 5.3 Completing a lesson (planned)

```
Frontend
  → POST /api/v1/lessons/:id/complete
Backend
  → exercises module grades answers
  → progress module records LessonProgress + XP events
  → gamification module updates streak / level / achievements
  → recommendations module may invalidate cached next-step hints
  → responds with updated progress summary
```

### 5.4 AI tutor turn (planned)

```
Frontend
  → POST /api/v1/ai/conversations/:id/messages
Backend (ai module)
  → loads conversation + learner context from DB
  → AI layer builds prompt, selects provider, calls provider
  → validates structured output, persists AIMessage
  → returns assistant message
```

Details: `project-map/data-flow.md`.

## 6. Cross-cutting concerns

- **Authentication/authorization** — email/password authentication is
  implemented: argon2id hashing, short-lived HS256 access JWTs, rotating refresh
  tokens stored hashed in an HttpOnly cookie, with reuse detection. `auth`,
  `users` and `progress` modules exist; RBAC (`ADMIN`) and ownership-scoped
  resources arrive with the learning catalog. See `docs/authentication.md`.
- **Validation** — Pydantic/FastAPI at the edge; domain invariants in services.
- **Error handling** — exception handlers map errors to a stable JSON envelope
  (`app/core/errors.py`).
- **Logging** — Python `logging` via uvicorn. Structured logging and request
  correlation ids are deferred. Never log passwords, tokens or raw AI prompts
  containing PII.
- **Rate limiting** — planned with auth/AI; not present yet.
- **Security** — see `docs/security.md`.
- **Testing** — see `docs/testing.md` and `plans/testing-plan.md`.

## 7. API

Versioned REST at `/api/v1`. Resource map and contracts: `docs/api.md`.
Conventions: JSON, `camelCase` fields, cursor pagination for large lists, and a
consistent error envelope.

## 8. Scaling path (deliberately deferred)

Optimize only when there is evidence:

1. Vertical scaling + a Postgres connection pool.
2. Read replicas / caching (Redis) for hot reads.
3. Extract the AI layer into a service **only if** it needs independent scaling,
   language or deployment cadence.
4. Split a module into a service **only if** its scaling or ownership justifies
   the operational cost.

## 9. Decisions and open questions

Decisions affecting the whole system are recorded in `plans/milestones.md`
(Decisions log) and, for architectural choices, in `plans/roadmap.md`. Open
questions:

- Email provider for verification/reset (deferred).
- Billing provider (deferred until subscriptions).
- Whether speaking feedback needs an audio-capable provider (deferred).
