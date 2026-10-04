# Frontend Plan

> Aligns with `plans/roadmap.md` Stages 4 and 6. Stack: Next.js (App Router) +
> Tailwind + TanStack Query + Framer Motion. See `docs/frontend.md`.

## Phase 1 — Scaffold

- [ ] `@fleng/frontend` package with Next.js (App Router) + TypeScript strict.
- [ ] Tailwind configured with design tokens from `design/`.
- [ ] Base layout, fonts (`next/font`), theme provider (dark default).
- [ ] `components/ui` primitives: Button, Input, Card, Badge, Dialog, Skeleton.
- [ ] Typed API client + error normalisation + auth/refresh handling.

## Phase 2 — Auth & shell

- [ ] `(auth)` routes: login, register, forgot/reset password.
- [ ] `(app)` shell: sidebar/topbar navigation, profile menu, responsive.
- [ ] Route protection based on session state; redirect on refresh failure.

## Phase 3 — Core learning screens

- [ ] Dashboard: streak, XP/level, continue-learning, daily goal.
- [ ] Learn: course list + course detail.
- [ ] Lessons: lesson player with exercise components per type; submit/grade.
- [ ] Progress: summary, per-course and per-skill views.
- [ ] Vocabulary: word list, add/remove, review session.

## Phase 4 — AI tutor

- [ ] AI Tutor chat UI (streaming deferred; simple request/response first).
- [ ] Writing correction view.
- [ ] Recommendations surfaced on dashboard.

## Phase 5 — Remaining sections

- [ ] Practice, Speaking, Listening, Reading, Writing, Grammar landing views.
- [ ] Challenges + leaderboard.
- [ ] Profile & Settings (profile, goals, language, theme, account).

## Phase 6 — Quality

- [ ] Playwright critical flows: auth, lesson completion, vocabulary review,
      AI turn.
- [ ] Accessibility pass (WCAG AA): focus, contrast, reduced motion.
- [ ] Performance pass: fonts/images, bundle review.

## Visual direction

Premium dark, purple/violet + blue/cyan accents, subtle gradients,
glassmorphism, modern typography, smooth motion. Tokens and rules live in
`design/`; no ad-hoc colors or spacing in components.

## Risks / watch-items

- Avoid over-componentising early; build screens, extract shared UI when reused.
- Keep server/client component boundaries intentional (`"use client"` only where
  needed).
- Streaming and voice are deferred; do not build abstractions for them now.
