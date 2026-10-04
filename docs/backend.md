# Backend

> Status: **design** (pre-implementation). Stack: NestJS + Prisma + PostgreSQL.

## 1. Responsibilities

The backend is the only part of the system allowed to make decisions about data:
validation, authorization, business rules, persistence and AI orchestration.
The frontend and AI library never reach the database.

## 2. Project structure (planned)

```
backend/
├── src/
│   ├── main.ts                 # bootstrap, global pipes/filters, helmet, CORS
│   ├── app.module.ts           # composes feature modules
│   ├── config/                 # typed, validated configuration
│   ├── common/                 # cross-cutting: guards, filters, pipes,
│   │                           # interceptors, decorators, base errors, DTOs
│   ├── prisma/                 # PrismaModule + PrismaService (connection lifecycle)
│   └── modules/
│       ├── auth/
│       ├── users/
│       ├── catalog/            # courses, lessons
│       ├── content/            # grammar, reading, listening materials
│       ├── exercises/          # exercise definitions, submissions, grading
│       ├── vocabulary/         # words, user vocabulary, flashcards/reviews
│       ├── progress/
│       ├── gamification/       # streaks, XP, levels, achievements
│       ├── challenges/
│       ├── recommendations/
│       ├── ai/                 # wraps @fleng/ai, owns AI persistence
│       ├── notifications/
│       ├── subscriptions/
│       └── analytics/
├── prisma/
│   ├── schema.prisma
│   └── migrations/
└── test/                       # API e2e (Supertest)
```

### Module internal structure

```
modules/<name>/
├── <name>.module.ts
├── <name>.controller.ts        # HTTP only
├── <name>.service.ts           # business rules, transaction boundaries
├── <name>.repository.ts        # Prisma access, returns domain objects
├── dto/                        # request/response DTOs + validation
├── entities/ (optional)        # domain types if Prisma models are not enough
└── <name>.service.spec.ts      # unit tests
```

Feature modules are only added when the feature exists. The list above is the
target, not a mandate to scaffold empty modules.

## 3. Request lifecycle

```
HTTP request
 → helmet / CORS (main.ts)
 → global ValidationPipe (whitelist, transform)
 → AuthGuard (JWT) + RolesGuard
 → controller (thin) → service (business logic)
 → repository → Prisma → PostgreSQL
 → interceptor (logging, serialization)
 → exception filter (on error)
 → JSON response
```

Every response uses the same envelope conventions and every error maps to the
standard error shape described in `docs/api.md`.

## 4. Cross-cutting concerns

- **Configuration** — `config/` validates env vars on startup (fail fast). No
  `process.env` reads scattered through modules.
- **Validation** — DTOs with `class-validator`; `whitelist: true`,
  `forbidNonWhitelisted: true`, `transform: true`.
- **Errors** — domain exceptions (`NotFoundError`, `ConflictError`,
  `ForbiddenError`, `ValidationError`) mapped centrally. No leaking stack traces
  or provider errors.
- **Logging** — Pino structured logs; a request correlation id per request; never
  log passwords, tokens or raw AI prompts containing PII.
- **Auth** — see `docs/authentication.md`.
- **Rate limiting** — global baseline plus stricter limits on auth and AI.

## 5. Transactions and consistency

- Writes that span aggregates (e.g. lesson completion touching progress,
  gamification and analytics) run in a Prisma transaction or are coordinated by
  the owning service with an explicit, documented sequence.
- Services define transaction boundaries; repositories accept a transaction
  client so they can participate without opening nested transactions.

## 6. Testing

| Level       | Tool              | Scope |
| ----------- | ----------------- | ----- |
| Unit        | Vitest            | services, pure logic, guards |
| Integration | Vitest + test DB  | repositories, transactions |
| API e2e     | Supertest         | endpoints, auth, validation |

Rules: no network calls to real AI providers in tests (use `mock` provider),
tests must be deterministic, and each module ships tests with its first feature.

## 7. Conventions

- Controllers return DTOs, never Prisma models directly.
- One exported service class per module; do not create pass-through wrappers.
- Prefer explicit code over clever abstractions (see `AGENTS.md` rule 2/9).
- No cross-module repository imports.

## 8. Build & run (intended)

```
pnpm --filter @fleng/backend dev
pnpm --filter @fleng/backend build
pnpm --filter @fleng/backend test
```

See `plans/backend-plan.md` for implementation order.
