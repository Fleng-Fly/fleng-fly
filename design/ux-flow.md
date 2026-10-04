# UX Flows

> Key journeys. Each flow lists the happy path and important edge/failure states.
> Flows align with the API in `docs/api.md`.

## 1. Onboarding & authentication

```
Landing → Register → (verify email) → Login → Dashboard
```

- Register: inline validation, clear password rules, generic error on conflict.
- Login: generic error on bad credentials (no enumeration), rate-limit message
  when exceeded.
- Session: silent refresh; on refresh failure → redirect to Login with a notice.
- Edge: already-authenticated user visiting auth pages is redirected to Dashboard.

## 2. First learning session

```
Dashboard → Continue learning → Lesson → Exercise → Submit → Feedback → … → Completion
```

- Empty state for new users: "Choose a course" CTA.
- Exercise feedback is immediate and inline; mistakes explain the rule.
- Completion screen shows score, XP gained, streak update, and a next action.
- Resume: leaving and returning restores lesson progress.

## 3. Vocabulary review (SRS)

```
Vocabulary → Review due → Flashcard → Rate (again/hard/good/easy) → Next → Summary
```

- Due count visible before starting.
- Empty state when nothing is due.
- Rating updates scheduling; off-by-default audio/pronunciation later.

## 4. AI tutor turn

```
AI Tutor → New/choose conversation → Type message → Send → Assistant reply
```

- Suggested prompts reduce blank-page friction.
- Loading indicator while the provider responds; timeout → clear retry.
- Rate-limit message when per-user limit is hit.
- Conversation history persists across sessions.

## 5. Writing correction

```
Writing practice → Prompt → Draft → Submit → Correction view (suggestions) → Revise
```

- Suggestions are attached to text spans; the original is preserved.
- AI unavailable → graceful message; the draft is never lost.

## 6. Progress check

```
Progress → Summary → Per-skill → Activity timeline
```

- Data loads as one summary request where possible (avoid many round trips).
- Empty state for no activity yet.

## 7. Mobile navigation

```
Topbar (streak/XP/profile) + Drawer/Bottom nav (primary sections)
```

- Primary sections reachable within one tap.
- Lesson player is full-screen and distraction-free.

## Global interaction rules

- Every async action has loading, success and error feedback.
- Destructive actions (delete account, reset progress) require confirmation.
- Optimistic updates only where rollback is trivial; otherwise show progress.
- Never block the core learning flow on an AI failure.
- Respect reduced-motion; keep transitions short.

## Error message principles

- Say what happened, why (if useful) and what the user can do next.
- No internal codes or provider details in the UI; show a friendly message and
  keep the technical `requestId` available for support.
