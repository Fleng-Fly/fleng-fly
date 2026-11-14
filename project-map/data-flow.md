# Project Map — Data Flow

> Status: M2/M3 implemented. Details: `docs/architecture.md §5`, `docs/api.md`,
> `docs/database.md`.

## Flow 1 — Frontend loads backend status (implemented)

```
Browser loads index.html → js/home.js
  → mountBackendStatus() → getHealth() → apiFetch('/health')
  → GET /api/v1/health  (same origin as the page)
  → FastAPI router → get_health(db) → `SELECT 1` in try/except
  → 200 { status, service, timestamp, database: up|down }
  → badge shows "Backend ● Online · db up|down" or "● Offline" on error
```

Refetches every 15s. When the backend is unreachable, the client throws
`ApiError(status 0, NETWORK_ERROR)` and the UI shows Offline — it never crashes.

## Flow 2 — Authentication & session (implemented)

Public registration is anonymous: BodyLimit (413 if oversized) → CORS (OPTIONS
preflight 200/400; POST continues) → exception handling/router → get_db/settings
and payload validation → `_assert_trusted_origin` (403 `Origin not allowed`) →
IP rate limit (429) → register user/session → 201 + Secure HttpOnly cookie.
No bearer/session dependency is attached to auth registration or its parent router.
Origin denial occurs before quota writes and user/session creation. The guard
accepts the ASGI request's own origin or an exact `CORS_ORIGIN` entry, and logs
bounded, escaped Origin/Host plus scheme on rejection without bodies or tokens.
Both public HTTPS origins must be explicit behind Render's TLS termination:
`https://fleng-fly.onrender.com,https://fleng.netlify.app`. See
[confirmed live 403 diagnosis](../docs/render-registration-origin-403.md).

```
Register/Login form (register.html / login.html + js/*.js)
  → login() → apiFetch('/auth/login')
  → POST /api/v1/auth/login {email,password}
  → auth service: argon2id verify → access JWT + opaque refresh token
  → refresh token stored SHA-256-hashed; raw value set as HttpOnly cookie
  → 200 { accessToken, user } → access token kept in memory (js/api.js)

Reload / expired access token
  → GET /users/me returns 401
  → client POSTs /auth/refresh (cookie) → server rotates the token
  → 200 { accessToken } → original request retried once

Reuse of a revoked refresh token
  → all of the user's active refresh tokens are revoked → 401 REFRESH_TOKEN_REUSED
```

## Flow 3 — Authenticated profile & progress (implemented)

```
/dashboard.html loads → js/dashboard.js main()
  → requireSession({ throwOnUnavailable: true }): js/session.js
  → GET /api/v1/users/me (Authorization: Bearer)
      → on 401, api.js refreshes once from the HttpOnly cookie and retries
      → no session → redirect to /login.html
  → get_current_user verifies the JWT → loads User + Profile
  → 200 { id, email, displayName, level, xp, createdAt }
  → GET /api/v1/progress/me, /streaks/me, /vocabulary/stats
  → progress service reads aggregate plus published course lesson counts
  → streak service reads activity days; vocabulary stats counts own learned words
  → UI shows name/level/XP, lesson completion ratio, estimated time,
    current course, streak and learned-word count; no fake data
  → API error → unavailable metric/error card + retry
  → search submits → GET /courses then /courses/{slug} for each published course
    → matching published courses/lessons shown as navigable results
```

Identity always comes from the access token subject; a user can only ever read
their own profile and progress.

## Flow 4 — Catalog read (implemented)

```
courses.html → js/courses.js → listCourses() → GET /api/v1/courses
  → catalog service: published courses + published-lesson counts, ordered → 200
  → cards (title, CEFR level, description, lesson count)

course.html?slug=... → getCourse(slug) → GET /api/v1/courses/{slug}
  → published course + published lessons (ordered) → 200 CourseDetail
  → missing/unpublished → 404 NOT_FOUND → friendly "not found" state

lesson.html?slug=... → getLesson(slug) → GET /api/v1/lessons/{slug}
  → published lesson of a published course → 200 LessonDetail
    (theory + public exercises, never answer keys)
  → theory rendered with textContent (headings / lists / paragraphs only)
```

Content is read-only and seeded by `backend/app/db/seed.py` (courses, lessons and
exercises).

## Flow 5 — Lesson start, submission and completion (implemented)

```
lesson.html?slug=... → startLesson(slug) → POST /api/v1/lessons/{slug}/start
  → get-or-create LessonProgress (in_progress) + Progress.lessons_started += 1
  → 200 LessonProgress (per-exercise state) → progress summary rendered

Answer an exercise → submitAnswer(slug, {exerciseId, answer, selfAssessment?})
  → POST /api/v1/lessons/{slug}/submit
  → exercises module: resolve lesson+exercise (404 if not the lesson's exercise)
  → validate answer shape (422 INVALID_ANSWER if malformed)
  → grade single_choice / text; record self-assessment for self_check
  → upsert ExerciseSubmission; award XP once (conditional UPDATE on xp_awarded)
  → recompute lesson completion; on first completion:
        LessonProgress -> completed
        Progress.lessons_completed += 1, study_minutes += estimatedMinutes
  → 200 SubmissionResult (correctness, +XP, revealed answer, explanation, lesson)
  → frontend updates the result area and the progress summary

GET /api/v1/progress/me
  → aggregate + derived exercisesCompleted + xp + per-course progress
```

XP is server-side only (never client-supplied) and cannot be farmed by retries.

The Lessons workspace adds a Theory tab from `LessonDetail.theory`, Practice
and Test views over the same exercises and submissions, and a Vocabulary tab.
The player reads `GET /lessons/{slug}/progress` before starting and resumes
from the first incomplete question. Progress includes the caller's latest
submitted answer for page reload; unsent drafts stay in memory. Vocabulary
calls `GET /vocabulary?lessonId=<lesson UUID>&offset=...&limit=30`, which filters
by both authenticated user and lesson. Dashboard reads the same persisted
progress through `GET /progress/me`.

## Flow 6 — Gamification (planned)

```
Lesson completion → XpEvent, Streak, Achievement updates
```

## Flow 7 — AI tutor turn (planned)

```
POST /ai/conversations/:id/messages
  → ai module: ownership check + context assembly + guardrails
  → AI layer builds prompt → provider.complete()
  → validate output → persist AIMessage(user + assistant)
```

## Data ownership summary

| Data                                                   | Writer                           | Reader             |
| ------------------------------------------------------ | -------------------------------- | ------------------ |
| Credentials, sessions/tokens                           | auth 🟢                          | auth 🟢            |
| User / Profile                                         | auth 🟢 (registration)           | users 🟢           |
| Progress (aggregate)                                   | exercises + progress 🟢          | progress 🟢        |
| Catalog/content (courses, lessons, exercises, answers) | catalog/exercises 🟢 (seed)      | logged-in users 🟢 |
| Submissions / lesson progress                          | exercises 🟢                     | progress 🟢        |
| XP                                                     | exercises 🟢 (once per exercise) | dashboard 🟢       |
| Streaks / achievements                                 | gamification 🔴                  | dashboards later   |
| AI conversations                                       | ai 🔴                            | ai 🔴              |

## Implemented extension flows — 2026-10-18

- Graded submission → learner row lock → existing deterministic grading/XP/progress
  → unique timezone-policy activity day → deterministic achievement rules → commit.
- Vocabulary review → ownership + learner lock → review record/due state → daily
  activity/achievement rules → commit. Adding words evaluates vocabulary awards.
- Reset request → shared IP/email hash counters → generic response → hashed expiring
  token and configurable SMTP delivery. Confirm → atomic token claim → password
  hash update + reset-token/refresh-session invalidation → commit.
- AI chat → auth/ownership/input checks → bounded read-only context/history → shared
  rate/budget/concurrency reservation commit → OpenRouter → validate complete output
  → atomic user+assistant pair + usage commit. Failure leaves history untouched.
- AI stream → same checks/reservation → upstream SSE parsing → delta events → only
  complete streams commit; otherwise error event/cancellation and failed accounting.
- Recommendations → latest incorrect exercise submissions grouped by lesson,
  unlearned vocabulary and next published lessons at CEFR level; no provider call.

AI has no privileged mutation tools or hidden official answer keys. Browser only
calls FastAPI. Provider transport is persistence-free and swappable via Protocol.

## SQLite startup

`npm run dev` or production `backend/run.py` → Python `app.db.prepare` → shared
config/async engine → rollback-only SQLite write probe → Alembic upgrade →
tables/columns validation → seed only if the course catalog is empty → uvicorn serves UI
and API. Users, refresh sessions, submissions, XP and progress persist in the
same ignored `backend/data/fleng.db` across restarts. PostgreSQL remains an
explicit DATABASE_URL choice with manual migrations. Production preparation runs
once before Uvicorn starts its single worker. Restart persistence requires the
same disk/file; free Render service restarts/redeploys/spin-down may discard it.

## Stabilized auth writes — 2026-10-28

Login/register → persistent IP limit (and normalized-email login limit) → bounded
Argon2 worker → identity lock and credential recheck → session commit.
Refresh → resolve hashed token owner → identity lock → conditional token claim →
successor + link + revocation commit together; replay commits whole-set revocation.
Password change/reset → same identity lock → hash update + refresh/reset token
revocation in one transaction → Settings returns to login (change flow).
Access JWTs retain their configured expiry. SQLite serializes writes through a
no-op UPDATE; PostgreSQL uses a user-row lock. Quota keys are hashed and shared
by workers through the existing database. See `docs/authentication.md`.


## Floating tutoring chat — 2026-11-01

Dashboard/Lessons → shared widget → authenticated POST `/ai/chat/stream` → existing
AI service (ownership, published lesson/exercise context, quotas, unique request
reservation) → OpenRouter → SSE delta → safe textContent UI → atomic AIConversation/
AIMessage pair + completed AIUsage → SSE done → saved conversation ID.
History returns only JWT-owned rows. Lesson/exercise identifiers are supplied by
Lessons; trusted context is loaded by backend. No AI-to-grading/progress mutation.


## Leaderboard

Protected page → shared session refresh → `GET /api/v1/leaderboard` →
gamification reads Profile XP + Progress totals → SQL global rank before limit →
batch activity for displayed learners and caller → existing streak calculation →
privacy-limited response → top cards/table/own position. No writes or XP awards.

## Courses Catalog → Course Details → Lesson — 2026-11-04

Shared session guard → workspace chrome → `GET /courses` + `GET /progress/me`
→ local title/description query AND CEFR filter → course card action
→ `/course.html?slug=...` → `GET /courses/{slug}` + `GET /progress/me`
→ `GET /lessons/{slug}/progress` for each published lesson → status/action
→ `/lesson.html?slug=...`. Only the existing lesson player starts/submits lessons.
Its lesson response provides `courseSlug` for returning to the correct details
page → Back to Courses. Page navigation/history restoration/tab return rereads
server progress; no second storage or XP writes on course pages. Failed reads
show errors/retry, and expired sessions redirect through the existing auth flow.

## Global AI lifecycle — 2026-11-04

Protected page → existing session guard → `setWorkspaceUser()` → singleton AI
(general mode; Lessons registers its context callback). Open → status + owned
conversation list → user-scoped selection → owned backend history. Submit →
authenticated FastAPI → strict request schema → validated lesson context → existing
rate/daily/concurrency reservation + input-token bound → OpenRouter → safe SSE text.
Logout/session-end → abort + clear private DOM/selection + cross-tab notification.
Navigation → destroy UI but retain user-scoped ID; cached restore revalidates session.

## Render HTTPS origin configuration — 2026-11-05

Render server environment `RENDER_EXTERNAL_URL` → Settings exact HTTPS-origin
validation → deduplicated merge with comma-separated `CORS_ORIGIN` → shared
CORSMiddleware + auth `_assert_trusted_origin()` allowlist. Thus public Render
HTTPS registration/login/refresh works even when upstream ASGI scheme is HTTP.
No forwarded header creates an allowlist entry. `run.py` still explicitly disables
proxy headers with empty TRUSTED_PROXY_IPS, overriding Render's Python
FORWARDED_ALLOW_IPS=* default. Configured trusted peers alone may supply scheme/IP;
Uvicorn ignores X-Forwarded-Host. DB/JWT/AI/learning flows are unchanged.


## Vocabulary flashcards — 2026-11-10

JWT user → own VocabularyItem OR published CourseVocabularyItem → at most 10 DB words → owned persisted FlashcardSession snapshot → owner completion → testReady + test-words → future Roma testing service. No XP/progress/review writes.


## A0–B2 curriculum — 2026-11-10

Versioned draft JSON → Pydantic structural validation/prerequisites → default DB dry-run → explicit draft import → human review + exact SHA acknowledgement → explicit publication in review DB → existing catalog/lesson/vocabulary APIs. No automatic startup import, production CLI writes or user/progress mutations.

## Curriculum QA — 2026-11-11

Existing draft bytes/SHA → existing Pydantic importer schemas + raw normalization
checks + actual single-choice grader probes → local source cache/provenance
(optional, never automatic downloads) → structural/linguistic JSON + Markdown.
Official local exports → explicit license-reviewed projection → private evidence
JSONL + input-hash manifest. Optional explicit AI opt-in → bounded existing
OpenRouter transport → human-review-only findings. Explicit safe-fix operation
requires source SHA → revalidated separate draft snapshot + diff; original and
publication workflow remain untouched. No database/progress/XP writes in QA.

## Local draft visual review — 2026-11-11

Fresh private /tmp directory → explicit isolated SQLite URL → Alembic + legacy
seed + existing unpublished curriculum import → new reviewer + private marker.
Dedicated loopback preview factory → standard login/JWT + reviewer UUID check →
existing Courses/Lessons JS → preview catalog/lesson/progress/dictionary read
wrappers → unchanged learning services (writes only to reviewer's isolated DB).
Normal app uses published-only defaults. QA UI submissions use a second database;
the prepared primary preview starts with zero learner progress. No publication,
production access or copy of personal accounts. Cleanup removes dedicated /tmp
folders after stopping their servers; repository screenshots remain available.
## PWA — 2026-11-13

Оновлено 2026-11-14: пропозиції завантажити/встановити додаток вилучено
з головної сторінки, навігації та offline-екрана; обробники встановлення й
окремі стилі видалено. `/install.html` зберігає лише довідку про доступ і прогрес.
Маніфест, іконки, реєстрація worker та offline fallback збережені;
кеш offline-екрана оновлено до v2. API й дані користувача не кешуються.
Далі: перевірка на фізичних пристроях.
Деталі: `docs/pwa-installation.md` (від кореня проєкту).

## Desktop — 2026-11-14

Launcher → user-data lock and persistent key → owned loopback worker → existing
SQLite preparation/migrations → normal FastAPI API and static frontend → dedicated
Edge/Chrome app window. Closing that window or losing the parent process closes
the worker lifetime pipe and stops only that server. Existing development data
is copied via SQLite backup only when the desktop database is absent.

## Database release verification — 2026-11-14

Push/PR → SQLite + disposable PostgreSQL CI → fresh Alembic schemas + drift check →
seed/import reruns → learner XP/vocabulary/card writes → pool reconnect → identity,
progress and session preservation + FK checks → required success aggregator.
Render waits for checks only after its external Auto-Deploy setting is configured.
No CI-to-production database connection or draft publication exists.

Explicit SQLite backup → read-only source + SQLite backup API → private new file →
integrity/FK checks + counts → operator-managed off-host storage/restore drill.

## Operator-only database transfer

Existing SQLite → new private online snapshot (read-only typed rows) → exact release/schema/FK validation → explicit PostgreSQL schema with table locks → FK-ordered import and refresh-token links → typed row/count reconciliation → default rollback or explicit --apply commit. No implicit application URL, publishing, deletion, upsert or production cutover. Logical recovery uses pg_dump → private archive → fresh isolated recovery database → row/API validation. See docs/05-database/transfer-and-recovery.md.

## npm run dev default catalog

Local file SQLite → private online backup before preparation → existing migrations → A0–B2 draft import without publication → loopback-only development factory → existing signed-in users see both legacy courses and all five drafts. Grading/progress keep existing user ownership and once-only XP. Production launcher and ordinary app factory never opt into these draft reads.
