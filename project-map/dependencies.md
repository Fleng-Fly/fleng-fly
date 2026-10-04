# Project Map — Dependencies

> Status: M1 implemented. Records the dependency policy and the **actually
> installed** libraries. Update when dependencies change.

## Dependency rules

1. Use what is already in the project; new dependencies need a real need
   (`AGENTS.md` rules 1–2).
2. Keep dependencies within their package; the root has orchestration tooling only.
3. The backend must never import frontend code, and vice versa.
4. The AI layer must not import FastAPI, SQLAlchemy or the database.
5. Prefer a small, well-maintained dependency over a bespoke solution — and a
   standard-library/framework feature over a dependency.

## Components

```
frontend/ (@fleng/frontend — pnpm workspace)
  (external) next, react, react-dom, @tanstack/react-query, framer-motion,
             tailwindcss, @tailwindcss/postcss
  (dev)      typescript, eslint, eslint-config-next, @eslint/eslintrc,
             vitest, @types/*

backend/ (fleng-backend — pip / venv)
  (runtime)  fastapi, uvicorn[standard], sqlalchemy[asyncio], asyncpg,
             pydantic-settings, alembic
  (dev)      pytest, pytest-asyncio, httpx, ruff, mypy

root/ (private)
  (dev)      prettier
  (scripts)  setup.mjs, dev.mjs  # Node stdlib only, no deps

ai/ (future Python package)
  (runtime)  provider SDK(s); schema validation  — not installed yet
```

## External dependencies (installed at M1)

### Backend

| Package | Purpose |
| ------- | ------- |
| fastapi | HTTP framework + validation + OpenAPI |
| uvicorn[standard] | ASGI server (`uvloop`, `httptools`, `watchfiles`) |
| sqlalchemy[asyncio] | ORM / SQL toolkit (async) |
| asyncpg | PostgreSQL async driver |
| pydantic-settings | Typed env configuration |
| alembic | Database migrations |

Dev: `pytest`, `pytest-asyncio`, `httpx` (TestClient transport), `ruff`
(lint + format), `mypy` (types).

### Frontend

| Package | Purpose |
| ------- | ------- |
| next, react, react-dom | App framework + UI |
| tailwindcss, @tailwindcss/postcss | Styling / design tokens |
| @tanstack/react-query | Server-state cache |
| framer-motion | Restrained animation |

Dev: `typescript`, `eslint`, `eslint-config-next`, `@eslint/eslintrc`, `vitest`,
`@types/node`, `@types/react`, `@types/react-dom`.

### Root

`prettier` (formatting JS/TS/Markdown). The `scripts/*.mjs` use only Node
built-ins (`child_process`, `fs`, `path`, `url`) — no concurrency dependency.

## Planned (not installed)

| Package | Component | Purpose | Introduced |
| ------- | --------- | ------- | ---------- |
| argon2-cffi | backend | password hashing | auth milestone |
| pyjwt | backend | access/refresh tokens | auth milestone |
| (AI provider SDK) | ai | LLM calls | AI milestone |
| playwright | frontend | browser e2e | later |

## Explicitly not used (yet)

| Rejected | Reason |
| -------- | ------ |
| Microservice framework / message broker | No proven need |
| GraphQL | REST suffices |
| Redis | Introduce only when caching/multi-instance rate limiting requires it |
| Celery / ARQ | No background jobs yet |
| Turborepo / Nx | Root Node scripts orchestrate the two packages |
| NestJS / Express / any Node.js backend framework | Backend is Python + FastAPI; TypeScript lives only in the frontend |
| An ORM other than SQLAlchemy (backend is Python) | SQLAlchemy 2 async is the chosen toolkit |

## Adding a dependency checklist

- [ ] Does the existing stack solve this already?
- [ ] Is it actively maintained and licensed acceptably?
- [ ] Is it used in more than a trivial way (no dependency for one function)?
- [ ] Is it scoped to the correct package?
- [ ] Is the decision recorded here (and in `plans/` if architectural)?
