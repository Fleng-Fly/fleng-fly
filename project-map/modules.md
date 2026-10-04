# Project Map — Modules

> Status: 🔴 documented only (no code yet). Durable design: `docs/backend.md`,
> `docs/frontend.md`. Update this file when a module is created, renamed or
> gains a dependency.

## Backend modules

Each module owns its controllers, services, repositories, DTOs and data. A module
may depend on another module's **service**, never its repository.

| Module | Status | Owns | Depends on |
| ------ | ------ | ---- | ---------- |
| `auth` | 🔴 | credentials, sessions, tokens | users (profile provisioning), notifications (email later) |
| `users` | 🔴 | profile, settings | — |
| `catalog` | 🔴 | courses, lessons | — |
| `content` | 🔴 | grammar/reading/listening materials | catalog (optional) |
| `exercises` | 🔴 | exercise definitions, submissions, grading | catalog |
| `vocabulary` | 🔴 | words, user vocabulary, flashcards/SRS | users |
| `progress` | 🔴 | lesson/course progress | catalog, exercises, gamification |
| `gamification` | 🔴 | XP, levels, streaks, achievements | progress (events) |
| `challenges` | 🔴 | challenge definitions, participation | progress, gamification |
| `recommendations` | 🔴 | next-step suggestions | progress, vocabulary, ai |
| `ai` | 🔴 | conversations, messages; wraps `@fleng/ai` | `@fleng/ai`, users, progress |
| `notifications` | 🔴 | in-app notification feed | users |
| `subscriptions` | 🔴 | plans, billing state | users |
| `analytics` | 🔴 | event recording | — |

### Cross-module dependency direction (allowed)

```
auth ──► users
progress ──► gamification
recommendations ──► ai ──► @fleng/ai
challenges ──► progress/gamification
```

Cycles are not allowed. If two modules need each other, extract the shared piece
or invert the dependency through an event/service interface owned by one side.

## Shared / infrastructure

| Component | Status | Purpose |
| --------- | ------ | ------- |
| `config/` | 🔴 | Validated env configuration |
| `common/` | 🔴 | Guards, pipes, filters, interceptors, base errors |
| `prisma/` | 🔴 | Prisma module/service, connection lifecycle |

## Frontend areas

| Area | Route | Status |
| ---- | ----- | ------ |
| Auth | `(auth)/login`, `/register`, reset | 🔴 |
| Dashboard | `/dashboard` | 🔴 |
| Learn | `/learn` | 🔴 |
| Lessons | `/lessons/[id]` | 🔴 |
| Vocabulary | `/vocabulary` | 🔴 |
| Practice hub | `/practice` | 🔴 |
| Speaking | `/practice/speaking` | 🔴 |
| Listening | `/practice/listening` | 🔴 |
| Reading | `/practice/reading` | 🔴 |
| Writing | `/practice/writing` | 🔴 |
| Grammar | `/grammar` | 🔴 |
| Challenges | `/challenges` | 🔴 |
| Progress | `/progress` | 🔴 |
| Profile | `/profile/[id]` | 🔴 |
| AI Tutor | `/ai-tutor` | 🔴 |
| Settings | `/settings` | 🔴 |

## AI layer (`@fleng/ai`)

| Part | Status | Purpose |
| ---- | ------ | ------- |
| `AIProvider` interface | 🔴 | Provider-agnostic completion API |
| `providers/mock` | 🔴 | Deterministic provider for tests |
| `providers/openai` | 🔴 | First real provider |
| `registry` | 🔴 | Config-driven provider selection |
| `prompts/*` | 🔴 | Per-capability prompt builders |
| `safety/` | 🔴 | Injection/output guardrails |
