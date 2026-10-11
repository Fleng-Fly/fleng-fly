# Project Map — Dependencies

> Status: M2/M3 implemented. Records the dependency policy and the **actually
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
frontend/ (static HTML/CSS/JS)
  (runtime)  none — no framework, no build step, no dependencies
  (dev)      none — no linter/bundler/test runner

backend/ (fleng-backend — pip / venv)
  (runtime)  fastapi, uvicorn[standard], sqlalchemy[asyncio], asyncpg,
             alembic, pydantic-settings, email-validator, argon2-cffi, pyjwt
  (dev)      pytest, pytest-asyncio, httpx, aiosqlite, ruff, mypy

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
| alembic | Database migrations |
| pydantic-settings | Typed env configuration |
| email-validator | Email format validation for `EmailStr` schemas |
| argon2-cffi | argon2id password hashing |
| pyjwt | Access-token (JWT) signing/verification |

Dev: `pytest`, `pytest-asyncio`, `httpx` (ASGI client), `aiosqlite` (in-memory
test database), `ruff` (lint + format), `mypy` (types).

### Frontend

None. The frontend is plain HTML5 + CSS3 + vanilla JavaScript (browser ES
modules and `fetch`), served statically by the backend. There is no bundler,
linter, test runner or runtime dependency.

### Root

`prettier` (formatting JS/TS/Markdown). The `scripts/*.mjs` use only Node
built-ins (`child_process`, `fs`, `path`, `url`) — no concurrency dependency.

## Planned (not installed)

| Package | Component | Purpose | Introduced |
| ------- | --------- | ------- | ---------- |
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
| NestJS / Express / any Node.js backend framework | Backend is Python + FastAPI |
| Next.js / React / Vue / Angular / Tailwind / TanStack Query / Framer Motion | Frontend is plain HTML/CSS/JS served statically; no framework or build step |
| TypeScript anywhere | Not used: frontend is vanilla JS, backend is Python |
| An ORM other than SQLAlchemy (backend is Python) | SQLAlchemy 2 async is the chosen toolkit |

## Adding a dependency checklist

- [ ] Does the existing stack solve this already?
- [ ] Is it actively maintained and licensed acceptably?
- [ ] Is it used in more than a trivial way (no dependency for one function)?
- [ ] Is it scoped to the correct package?
- [ ] Is the decision recorded here (and in `plans/` if architectural)?
