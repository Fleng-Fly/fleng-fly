# Pages

> Page/section inventory and intended layout. Routes mirror the App Router
> structure in `docs/frontend.md`. Build order is in `plans/frontend-plan.md`.

## Public / marketing

- **Landing** — hero (value proposition + CTA), feature highlights, social proof
  (when real), footer. Dark hero with subtle violet→cyan glow.
- **Pricing** — plans comparison (deferred; placeholder until billing exists).
- **Legal** — terms, privacy.

## Auth

- **Login** — email/password, link to register/forgot.
- **Register** — email/password/display name, terms consent.
- **Forgot / Reset Password** — email request and token-based reset.

All auth pages are centered cards on the dark background; no app shell.

## App shell

Persistent left sidebar (desktop) / drawer or bottom nav (mobile) + topbar with
streak, XP, notifications and profile menu.

### Dashboard `/dashboard`

Current `/dashboard.html` implementation follows the supplied Dashboard
description and palette: compact sidebar, catalog search, welcome card, quick
access, progress ring and current course. Exact Figma geometry and imagery are
not verified because the file/screenshots were inaccessible in this run.

- Greeting + daily goal ring.
- "Continue learning" card.
- Streak and XP/level summary.
- Recommended next steps (AI/rule-based).
- Recent activity.

### Learn `/learn`

- Course catalog (filters by level).
- Course detail: description, progress, lesson list with status.

### Lessons `/lessons/[id]`

- Lesson player: one exercise at a time, progress indicator, submit/continue.
- Feedback states (correct/incorrect) inline.
- Completion screen: score, XP gained, streak update, next lesson.

Current `/lesson.html?slug=...` implementation uses the Dashboard sidebar and
header, a data-driven lesson hero, Theory/Practice/Test/Vocabulary tabs, a
question card and a right-column current-test preview. “Use template” enters
Test; custom template creation is unavailable. Completion is a status banner
with a course link. The standalone score/next-lesson screen above remains a
design idea. Exact Figma comparison is pending access to the target frame.

### Vocabulary `/vocabulary`

- Word list with status and due counts.
- Add word / search dictionary.
- Review session: flashcards with rating controls.

### Practice `/practice`

- Hub linking to speaking, listening, reading, writing and grammar practice.
- Recommended practice based on weak skills.

### Speaking `/practice/speaking`

- Prompt, recorder, AI feedback (deferred until voice work).

### Listening `/practice/listening`

- Audio player, comprehension questions, transcript toggle.

### Reading `/practice/reading`

- Graded text, vocabulary highlights, comprehension questions.

### Writing `/practice/writing`

- Prompt, editor, AI correction with inline suggestions.

### Grammar `/grammar`

- Topic list, explanations, examples, linked exercises.

### Challenges `/challenges`

- Active challenges with progress/time remaining; leaderboard.

### Progress `/progress`

- Summary (XP, level, streak), per-skill breakdown, activity timeline.

### Profile `/profile/[id]`

- Public profile: display name, avatar, level, achievements, stats.

### AI Tutor `/ai-tutor`

- Conversation list + chat view; suggested prompts; scenario selection.

### Settings `/settings`

- Profile, learning goals, native language, notifications, appearance (dark
  default), account (logout, delete).

## Layout rules

- Consistent page header (title + actions), max content width ~1200px.
- Reading/lesson content constrained to ~720px for line length.
- Empty and loading states designed for every data-driven page.
- Mobile-first: every layout works down to 360px width.
