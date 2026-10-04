# backend/

API and business logic of Fleng. **Not implemented yet** — this directory
currently holds documentation only.

## Planned stack

- **NestJS** (TypeScript) as the modular-monolith framework
- **Prisma ORM** + **PostgreSQL**
- **JWT** access tokens + rotating refresh tokens (`argon2id` password hashing)
- **class-validator / class-transformer** for input validation
- **Pino** structured logging
- **Vitest** unit tests + **Supertest** API tests

## Modules

`auth`, `users`, `catalog`, `content`, `exercises`, `vocabulary`, `progress`,
`gamification`, `challenges`, `recommendations`, `ai`, `notifications`,
`subscriptions`, `analytics`.

Each module owns its controllers, services, repositories/DTOs and is imported
explicitly. No cross-module access to another module's repository.

## Where to look

- Plan: `plans/backend-plan.md`
- Architecture: `docs/backend.md`, `docs/architecture.md`
- Database: `docs/database.md`
- API: `docs/api.md`
- Security: `docs/security.md`

> When the app is scaffolded, replace this file with a real project README
> (scripts, structure, environment variables).
