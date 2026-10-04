# Architecture

> Status: **design** (pre-implementation). This document is the canonical
> description of how Fleng is intended to be built. Update it whenever the real
> architecture diverges.

## 1. Goals and constraints

- A web platform for learning English with structured content, interactive
  practice, gamified progress and AI assistance.
- Built and maintained by several agents/developers → strong conventions,
  explicit boundaries, small commits.
- Start simple and extensible. **No premature microservices.**
- TypeScript on every surface to share types and mental models.

Non-goals for the MVP:

- Native mobile apps, real-time multiplayer, or a custom ML training stack.
- Multi-region deployment, sharding, or event streaming.

## 2. Architectural style

**Modular monolith.**

- **Frontend** (Next.js) is a single deployable that renders the product and
  talks to the backend over HTTP/JSON.
- **Backend** (NestJS) is a single deployable, internally split into modules with
  explicit interfaces and dependency direction.
- **AI layer** (`@fleng/ai`) is a library imported by the backend. It isolates
  provider-specific code and prompt/response handling. It is *not* a service.
- **PostgreSQL** is the single source of persistent truth, accessed only through
  Prisma from the backend.

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
│ Backend — NestJS (modular monolith)                      │
│                                                          │
│  Cross-cutting: auth guard · validation pipe · logging   │
│                 error filter · rate limiting             │
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
       │ imports (in-process)
       ▼
┌──────────────────────────┐
│ @fleng/ai                │  providers · prompts · parsing · guardrails
└─────────────┬────────────┘
              │ HTTPS
              ▼
      External AI providers

              ▲
              │ Prisma
┌──────────────────────────┐
│ PostgreSQL               │
└──────────────────────────┘
```

## 3. Layer responsibilities

| Layer    | Owns                                                        | Must not |
| -------- | ----------------------------------------------------------- | -------- |
| Frontend | Rendering, routing, forms, client cache, design system      | Contain business rules, call AI providers directly, store secrets |
| Backend  | Business rules, validation, authz, persistence, orchestration | Contain UI concerns, expose provider-specific AI payloads |
| AI lib   | Provider clients, prompts, response parsing, guardrails      | Know about HTTP, NestJS, Prisma, or the database |
| Database | Data integrity, constraints, indexes                         | Be bypassed by raw SQL outside controlled migrations |

## 4. Backend module boundaries

Each module owns its data and exposes a service. Rules:

1. A module may import another module's **service**, never its repository.
2. Controllers do HTTP + auth + validation only; no business logic.
3. Repositories are thin Prisma wrappers; complex queries may live in a
   dedicated query service inside the module.
4. Cross-cutting concerns (auth, logging, validation, errors, rate limits) are
   implemented as guards/pipes/filters/interceptors, not per-module copies.

Modules, responsibilities and dependencies: `project-map/modules.md`.

## 5. Data flow (representative)

### 5.1 Completing a lesson

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

### 5.2 AI tutor turn

```
Frontend
  → POST /api/v1/ai/conversations/:id/messages
Backend (ai module)
  → loads conversation + learner context from DB
  → @fleng/ai builds prompt, selects provider, calls provider
  → validates structured output, persists AIMessage
  → returns assistant message
```

Details: `project-map/data-flow.md`.

## 6. Cross-cutting concerns

- **Authentication/authorization** — JWT access + rotating refresh; RBAC
  (`USER`, `ADMIN`). See `docs/authentication.md`.
- **Validation** — DTO validation at the edge; domain invariants in services.
- **Error handling** — a single exception filter maps domain errors to a stable
  JSON error envelope.
- **Logging** — structured JSON logs with request/correlation IDs.
- **Rate limiting** — tight on auth and AI endpoints.
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
