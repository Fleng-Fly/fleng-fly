# Project Map — Dependencies

> Status: 🔴 documented only. No `package.json` files exist yet, so this file
> records the **intended** dependency policy and graph. Update when packages land.

## Dependency rules

1. Use what is already in the project; new dependencies need a real need
   (`AGENTS.md` rules 1–2).
2. Keep dependencies within their package; the root is orchestration only.
3. The backend must never import frontend code, and vice versa.
4. `@fleng/ai` must not import backend code, NestJS or Prisma.
5. Prefer a small, well-maintained dependency over a bespoke solution — and a
   standard-library/built-in solution over a dependency.

## Package graph (target)

```
frontend (@fleng/frontend)
  └── (external) next, react, tailwind, framer-motion, @tanstack/react-query

backend (@fleng/backend)
  ├── @fleng/ai           # workspace dependency
  └── (external) @nestjs/*, @prisma/client, argon2, class-validator,
                 class-transformer, passport, passport-jwt, pino, helmet

ai (@fleng/ai)
  └── (external) provider SDK(s), zod (output schema validation)

root (private)
  └── orchestration scripts only; no runtime dependencies
```

Internal dependency direction is one-way: `backend → ai`. There is no
`ai → backend` or cross-app dependency.

## External dependencies (planned)

| Package | Package | Purpose | Introduced |
| ------- | ------- | ------- | ---------- |
| next, react, react-dom | frontend | app framework/UI | Stage 4 |
| tailwindcss | frontend | styling | Stage 4 |
| framer-motion | frontend | animation | Stage 4 |
| @tanstack/react-query | frontend | server state | Stage 4 |
| @nestjs/common, core | backend | framework | Stage 1 |
| @prisma/client, prisma | backend | ORM + migrations | Stage 1 |
| argon2 | backend | password hashing | Stage 1 |
| class-validator, class-transformer | backend | DTO validation | Stage 1 |
| @nestjs/passport, passport, passport-jwt | backend | auth | Stage 1 |
| pino, nestjs-pino | backend | logging | Stage 1 |
| helmet | backend | security headers | Stage 1 |
| @nestjs/throttler | backend | rate limiting | Stage 1/2 |
| zod | ai | response schema validation | Stage 5 |
| openai | ai | first provider | Stage 5 |
| vitest, supertest, playwright | dev | testing | Stage 1/4 |

## Explicitly not used (yet)

| Rejected | Reason |
| -------- | ------ |
| Microservice framework / message broker | No proven need |
| GraphQL | REST suffices |
| Redis | Introduce only when caching/multi-instance rate limiting requires it |
| ORM alternates (TypeORM/Drizzle) | Prisma chosen once; avoid churn |
| State libraries (Redux) | React + TanStack Query suffice until proven otherwise |

## Adding a dependency checklist

- [ ] Does the existing stack solve this already?
- [ ] Is it actively maintained and licensed acceptably?
- [ ] Is it used in more than a trivial way (no dependency for one function)?
- [ ] Is it scoped to the correct package?
- [ ] Is the decision recorded here (and in `plans/` if architectural)?
