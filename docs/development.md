# Development

> Status: **design** (pre-implementation). Commands become real when the first
> package manifests land. Nothing here should be treated as runnable yet.

## 1. Technology stack and rationale

| Area           | Choice                                                   | Why |
| -------------- | -------------------------------------------------------- | --- |
| Language       | TypeScript                                               | One language across the stack; shared types; large ecosystem |
| Package manager| pnpm workspaces                                          | Fast, space-efficient, first-class workspaces for the monorepo |
| Frontend       | Next.js (App Router)                                     | Routing, SSR/RSC, good DX; matches SEO + app needs |
| Styling        | Tailwind CSS                                             | Token-driven design system that matches `design/` |
| Animation      | Framer Motion                                            | Declarative, restrained motion |
| Server state   | TanStack Query                                           | Caching, retries, request de-duplication |
| Backend        | NestJS                                                   | Opinionated modules/DI fit a modular monolith and team consistency |
| ORM            | Prisma                                                   | Type-safe schema, migrations, good DX |
| Database       | PostgreSQL                                               | Relational integrity + JSONB flexibility |
| Auth           | JWT access + rotating refresh, argon2id                  | Stateless access, revocable refresh |
| AI             | `@fleng/ai` provider abstraction                         | Avoid vendor lock-in without a service boundary |
| Logging        | Pino                                                     | Structured, fast JSON logs |
| Tests          | Vitest, Supertest, Playwright                            | Fast unit/API tests + real browser e2e |
| DevOps         | Docker + docker compose                                  | Reproducible local environment |

### Rejected-for-now (deliberately not added)

- **Microservices / message broker** — no proven need; adds operational cost.
- **Redis** — introduce only when caching/rate-limit persistence justifies it.
- **GraphQL** — REST is sufficient for the initial resource model.
- **A Python AI service** — call provider APIs from TypeScript; revisit only if
  a capability genuinely needs the Python ecosystem.

Adding any of these requires a written justification in the relevant plan.

## 2. Monorepo layout

```
/
├── frontend/     # @fleng/frontend — Next.js app
├── backend/      # @fleng/backend  — NestJS API
├── ai/           # @fleng/ai       — provider-agnostic AI library
├── docs/ plans/ design/ project-map/
├── package.json          # workspace root (scripts only, private)
├── pnpm-workspace.yaml   # workspace globs
└── .env.example          # documented, non-secret defaults
```

The root `package.json` is private and only orchestrates scripts. Each package
owns its dependencies.

## 3. Prerequisites

- Node.js LTS (>= 20)
- pnpm (>= 9)
- Docker + docker compose (for PostgreSQL locally)
- Git

## 4. Getting started (intended)

```bash
git clone <repo>
cd fleng
pnpm install

cp .env.example .env
# edit .env locally — never commit it

docker compose up -d db
pnpm db:migrate
pnpm dev            # runs frontend + backend concurrently
```

## 5. Environment variables

All secrets live in `.env` (git-ignored). `.env.example` documents names with
safe placeholders. Never commit real keys.

Core variables (names final, values TBD):

| Variable                 | Used by  | Purpose |
| ------------------------ | -------- | ------- |
| `NODE_ENV`               | all      | `development` / `test` / `production` |
| `DATABASE_URL`           | backend  | PostgreSQL connection string |
| `JWT_ACCESS_SECRET`      | backend  | Access-token signing |
| `JWT_REFRESH_SECRET`     | backend  | Refresh-token signing |
| `ACCESS_TOKEN_TTL`       | backend  | e.g. `15m` |
| `REFRESH_TOKEN_TTL`      | backend  | e.g. `30d` |
| `AI_PROVIDER`            | ai/backend | `openai` / `anthropic` / `mock` |
| `AI_API_KEY`             | ai       | Provider key (server-side only) |
| `AI_MODEL`               | ai       | Default model id |
| `CORS_ORIGIN`            | backend  | Allowed frontend origin(s) |
| `NEXT_PUBLIC_API_URL`    | frontend | Backend base URL (public by design) |

Secrets are **never** exposed to the frontend; only `NEXT_PUBLIC_*` values ship
to the browser.

## 6. Scripts (intended, at repo root)

| Script            | Effect |
| ----------------- | ------ |
| `pnpm dev`        | Run frontend + backend in watch mode |
| `pnpm build`      | Build all packages |
| `pnpm lint`       | ESLint across the workspace |
| `pnpm format`     | Prettier write |
| `pnpm typecheck`  | `tsc --noEmit` across packages |
| `pnpm test`       | Unit + API tests |
| `pnpm test:e2e`   | Playwright |
| `pnpm db:migrate` | Prisma migrate dev |
| `pnpm db:generate` | Regenerate the Prisma client |
| `pnpm db:studio`  | Prisma Studio |

## 7. Code conventions

- TypeScript `strict` mode; avoid `any` (use `unknown` + narrowing).
- Prettier for formatting; ESLint for correctness. Formatting is not debated.
- File naming: see `docs/backend.md` and `docs/frontend.md`.
- Commit messages: `type: summary` (`chore`, `docs`, `feat`, `fix`, `refactor`,
  `test`). One logical change per commit.
- Never commit `.env`, secrets, generated clients, or build output.

## 8. Definition of Done

Per `AGENTS.md`: working code/docs, updated `project-map/`, updated `plans/`,
tests where applicable, an independent self-review, and small logical commits.

## 9. Troubleshooting

- **Workspace package not found** — run `pnpm install` from the repo root.
- **Database connection refused** — ensure `docker compose up -d db` is running
  and `DATABASE_URL` matches.
- **Prisma client stale** — run `pnpm db:generate` after schema changes.
