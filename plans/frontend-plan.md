# Frontend Plan

> Aligns with `plans/roadmap.md` Stages 4 and 6. Stack: Next.js (App Router) +
> Tailwind + TanStack Query + Framer Motion. See `docs/frontend.md`.

## Phase 1 — Scaffold

- [x] `@fleng/frontend` package with Next.js (App Router) + TypeScript strict.
- [x] Tailwind configured with design tokens from `design/`.
- [x] Base layout, fonts (`next/font`), dark default.
- [x] `components/ui` primitives: Button, Card, Badge. *(Input, Dialog,
      Skeleton still to add when needed.)*
- [x] Typed API client + error normalisation + auth/refresh handling.

## Phase 2 — Auth & shell

- [x] Auth routes: login, register. *(Forgot/reset password pending.)*
- [x] Route protection based on session state; redirect on missing session.
- [ ] `(app)` shell: sidebar/topbar navigation, profile menu, responsive.

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
