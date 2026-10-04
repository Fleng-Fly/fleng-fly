# Milestones & Status

> Living status board. Keep in sync with `plans/roadmap.md` and the actual repo.
> Legend: ✅ completed · 🚧 in progress · ⛔ blocked · ⬜ next/not started ·
> ❌ cancelled.

Last updated: Stage 0 (Foundation).

| # | Milestone | Status | Notes |
| - | --------- | ------ | ----- |
| M0 | Repository foundation (docs, map, plans, design) | ✅ completed | This commit; no app code |
| M1 | Monorepo + backend bootstrap | ⬜ next | pnpm workspaces, NestJS skeleton, config, logging, validation, error filter |
| M2 | Database model (identity, users, catalog) | ⬜ next | Prisma schema + migrations for MVP entities only |
| M3 | Authentication & profiles | ⬜ next | register/login/refresh/logout, `/users/me` |
| M4 | Catalog & learning | ⬜ | courses, lessons, exercises, submissions, progress |
| M5 | Vocabulary + SRS | ⬜ | words, user vocabulary, flashcards |
| M6 | Gamification | ⬜ | XP, levels, streaks, achievements |
| M7 | Frontend MVP | ⬜ | app shell + core screens + design system |
| M8 | AI tutor | ⬜ | provider abstraction + tutor + writing correction |
| M9 | Polish & launch | ⬜ | practice depth, notifications, analytics, deploy |

## Blocked

Nothing is blocked.

## Immediate next actions (M1–M3)

1. Create root workspace manifests (`package.json`, `pnpm-workspace.yaml`) and
   the three package skeletons.
2. Bootstrap the NestJS backend with `config/`, `prisma/`, `common/`.
3. Implement the identity/user/catalog Prisma schema and migrations.
4. Implement auth + profile endpoints with tests and the security checklist.

## Decisions log

| Date | Decision | Rationale |
| ---- | -------- | --------- |
| Foundation | Modular monolith, TypeScript everywhere | Simplicity, shared types, team consistency (`AGENTS.md` 9) |
| Foundation | AI as a library, not a service | No proven scaling/language need; avoid premature microservice |
| Foundation | PostgreSQL + Prisma | Relational integrity + strong DX |
| Foundation | pnpm workspaces | Efficient monorepo without extra orchestration tooling |
