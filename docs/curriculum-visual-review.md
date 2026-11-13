# Local curriculum visual review

Prepared and verified on 2026-11-11. No commit, push, production connection,
publication or application database write. The preview uses the existing Courses,
Course and Lessons pages, with the existing authentication and learning services.

## Start the prepared preview

Run from the repository root, in a terminal that will stay open:

```bash
backend/.venv/bin/python scripts/preview_curriculum.py start
```

Then open <http://127.0.0.1:3011/login.html>. The command prints the local reviewer
email and randomly generated password. Sign in normally and open
<http://127.0.0.1:3011/courses.html>. Login initially redirects to the existing
Dashboard; navigate to Courses to review the curriculum. No password/JWT key is
stored in the repository. The preview server was stopped after QA so this
command can claim the port. Stop your server with Ctrl+C before cleanup/restart.

The prepared directory in this environment is
`/tmp/fleng-curriculum-preview-1000`. Default paths use the current Unix UID.
A prepared database persists across server restarts, but `/tmp` may be cleared
on reboot. If the directory has disappeared, prepare it first:

```bash
backend/.venv/bin/python scripts/preview_curriculum.py prepare
backend/.venv/bin/python scripts/preview_curriculum.py start
```

`prepare` intentionally refuses an existing directory. It cannot overwrite an
existing preview or another database. For an independent fresh review, use a
new dedicated directory and port:

```bash
backend/.venv/bin/python scripts/preview_curriculum.py prepare \
  --directory /tmp/fleng-second-review --port 3013
backend/.venv/bin/python scripts/preview_curriculum.py start \
  --directory /tmp/fleng-second-review --port 3013
```

The existing backend virtualenv is required; no new dependencies/build step.
Do not use `npm run dev` for this preview: that command uses normal application
configuration. The preview launcher explicitly supplies its own SQLite URL,
random JWT signing key, distinct refresh-cookie name, loopback origin and static
frontend path, and disables AI and SMTP. Existing auth, CSRF, rate limits,
object ownership and answer-key secrecy remain active.

## Opening the draft courses

The authenticated Courses catalog contains seven real source-backed courses:
the two existing seed courses and these five unpublished drafts:

| Level | Course URL | Lessons / words / exercises |
| --- | --- | --- |
| A0 | <http://127.0.0.1:3011/course.html?slug=fleng-a0> | 10 / 100 / 80 |
| A1 | <http://127.0.0.1:3011/course.html?slug=fleng-a1> | 10 / 100 / 80 |
| A2 | <http://127.0.0.1:3011/course.html?slug=fleng-a2> | 10 / 100 / 80 |
| B1 | <http://127.0.0.1:3011/course.html?slug=fleng-b1> | 10 / 100 / 80 |
| B2 | <http://127.0.0.1:3011/course.html?slug=fleng-b2> | 10 / 100 / 80 |

Use the existing level buttons/search, open a course, then any lesson. The
player defaults to Test; choose Theory to review explanations, worked examples,
reading and the ten Ukrainian vocabulary translations. Practice shows the
existing exercise forms. Lesson breadcrumb returns to its course; the course
breadcrumb returns to Courses. There are no new direct next/previous-lesson
buttons; lesson-to-lesson navigation uses the course list. Question navigation
remains the existing player behavior.

`Vocabulary` is the existing **personal saved words** tab. It correctly starts
empty for the new reviewer. The ten curriculum words are shown under Vocabulary
inside Theory; all 100 course dictionary records are also available through the
authenticated `/api/v1/vocabulary/course-words?courseId=UUID&limit=100` endpoint.
No personal words, fake learning statistics or placeholder courses were inserted.

## Isolation and implementation

`prepare` creates a private 0700 directory and 0600 database/marker. It runs the
existing Alembic migrations, `seed_catalog`, and
`import_curriculum(..., apply=True)` **without** a reviewed publication SHA.
Only a new reviewer account is created, through the existing registration service.
It does not copy personal accounts/progress or inspect a production database.
At audit time `backend/data/fleng.db` did not exist and was not created.

Prepared totals: **7 courses, 56 lessons, 418 exercises, 500 course words**.
All five imported courses and 50 imported lessons retain `is_published=False`.
The canonical draft SHA is
`27ab5cdc8cdadbfc85353cea58fc2584459c130aea460cf391a2e5d67b108013`.
Changing the packaged draft requires preparing a new directory; startup rejects
a marker with a different SHA.

The separate `app.preview:create_preview_app` factory validates development mode,
the fixed preview filename, private owned marker/database, matching random JWT
key and isolated refresh-cookie name. It refuses AI/SMTP-enabled configuration,
production, the normal database URL and symlinks. A loopback client check and
TrustedHost allowlist restrict requests; Uvicorn binds 127.0.0.1 with proxy
headers disabled. Do not reverse-proxy, tunnel or deploy this local preview.

Only the marker's reviewer UUID may access the preview content routes, after
normal JWT authentication. Another registered account receives 403; anonymous
requests receive 401. The normal app factory has no preview routes and continues
to hide drafts, even if `include_drafts=true` is supplied in a query string.

Existing read services accept an internal keyword `include_drafts=False`;
only authenticated preview wrappers set it to True. This includes per-course
progress reads so the existing frontend receives real counts for all visible
courses. The existing start/submit/grader/XP services are reused unchanged. API
interactions naturally record only the isolated reviewer's progress in its
preview database. No production or pre-existing learner is affected.

A `.server.lock` prevents simultaneous launcher instances against the same
preview database. The directory is a local single-user review artifact, not an
admin authorization system or a production publishing mechanism.

## Verification and screenshots

- Full pytest after preview implementation: **375 passed, 15 skipped**.
- Final targeted rerun after adding launcher filesystem guards: **13 passed**.
- Existing Courses DOM regressions: **7 passed**.
- Ruff (`app tests` and both new scripts), mypy (**77 source files**) and
  `git diff --check`: passed. No new migration or dependency.
- Actual preview DB migration/seed/draft import succeeded: 955 draft rows added.
- Read-only HTTP sweep checked all five draft courses, 50 rendered lesson
  payloads, all 500 word/course associations and all 400 answer keys through the
  existing grader, including rejected distractors. Theory and Ukrainian strings
  equal the packaged source; public lesson payloads omit answer keys.
- Primary preview reviewer remains **0 XP / 0 started / 0 completed lessons**.
  Browser clicks/submissions used a separate QA database at
  `/tmp/fleng-curriculum-qa-1000`, port 3012. QA/browser processes were stopped.
- Firefox **159.0.1**, isolated temporary profile, actual HTML/CSS/JS through
  WebDriver BiDi: **122 checks, zero horizontal-overflow/replacement-character
  failures**, 16 screenshots. Viewports: desktop 1440×1000, mobile 390×844.
  All 50 lessons were opened at each width; lesson theory/examples/translations
  were checked in the rendered DOM. Each course's final lesson had an answer
  submitted through the real Practice form at each width (10 UI submissions).
  Course/lesson/catalog link navigation worked.

The screenshot helper waits for the existing reveal animations before capture;
the earlier captures taken during opacity transitions were replaced. No CSS or
page design changes were needed. Headless Firefox viewport emulation is not a
claim of testing a physical mobile device or every supported browser.

Artifacts:

- [HTTP results](../reports/curriculum-preview/http-review.json)
- [Browser results](../reports/curriculum-preview/visual/browser-review.json)
- [Desktop catalog](../reports/curriculum-preview/visual/courses-desktop.png)
- [Mobile catalog](../reports/curriculum-preview/visual/courses-mobile.png)
- [Desktop A0 theory](../reports/curriculum-preview/visual/fleng-a0-theory-desktop.png)
- [Mobile B2 theory](../reports/curriculum-preview/visual/fleng-b2-theory-mobile.png)
- [Mobile exercise](../reports/curriculum-preview/visual/exercise-b2-mobile.png)

Reproducible optional browser QA uses the existing `websockets` dependency and a
Firefox installation; no browser packages were added. Example in separate
terminals, using a new QA directory/output each time:

```bash
backend/.venv/bin/python scripts/preview_curriculum.py prepare \
  --directory /tmp/fleng-qa-new --port 3012
backend/.venv/bin/python scripts/preview_curriculum.py start \
  --directory /tmp/fleng-qa-new --port 3012
```

```bash
mkdir -m 700 /tmp/fleng-firefox-new
/opt/firefox/firefox --headless --no-remote \
  --profile /tmp/fleng-firefox-new --remote-debugging-port 9228 about:blank
```

```bash
backend/.venv/bin/python scripts/review_curriculum_browser.py \
  --directory /tmp/fleng-qa-new --url http://127.0.0.1:3012 \
  --bidi ws://127.0.0.1:9228/session --output /tmp/fleng-browser-new-report
```

Use a fresh dedicated browser session; an existing active BiDi session cannot be
replaced. [Mozilla's connection documentation](https://developer.mozilla.org/en-US/docs/Web/WebDriver/How_to/Create_BiDi_connection)
describes the loopback endpoint. Stop Firefox and the QA server with Ctrl+C.

## Findings and remaining limitations

1. Drafts were hidden at several boundaries (catalog, lesson resolution, progress
   totals and course dictionary). The isolated authenticated preview resolves
   these consistently while leaving ordinary/public queries unchanged.
2. The personal Vocabulary tab is not the course dictionary. It remains empty
   honestly; curriculum words are available in Theory and the course-words API.
3. Lessons initially open Test, not Theory. Use the existing tabs; no redesign.
4. The global floating AI launcher remains visible although AI is disabled.
   On mobile it can overlap a small area of text near the bottom of the viewport;
   scrolling moves the text clear. It stayed inside the viewport. This existing
   widget behavior was recorded, not changed as part of curriculum preview.
5. No broken Ukrainian text, missing theory/examples, failing lesson navigation
   or horizontal page overflow was found at the tested widths. Existing
   source-validation language-review limitations remain: this visual pass does
   not approve grammar/translations or certify CEFR proficiency.

Self-review covered default-public behavior, reviewer-only draft access, key and
cookie separation, production/remote/Host/CSRF refusal, answer secrecy,
filesystem collision/symlink/privacy checks, data/source identity and unchanged
XP semantics. Existing uncommitted work was preserved. Added `app/preview.py`,
`test_curriculum_preview.py`, two root scripts, this document and report artifacts;
updated main app's explicit development-only router injection and four existing
read services. Project map and plan entries describe the boundary below.

## Remove the test database

First stop the preview server with Ctrl+C. Then remove **only its dedicated
preview directory**, including its local credentials and SQLite journal files:

```bash
rm -r -- /tmp/fleng-curriculum-preview-1000
```

The separate QA directory can also be removed after its server has stopped:

```bash
rm -r -- /tmp/fleng-curriculum-qa-1000
```

These paths are not `backend/data/` and are never production connection URLs.
Use your explicitly selected directory if you supplied `--directory`; do not
replace either path with a parent directory. Screenshots/reports in the repository
remain review artifacts. Do not run cleanup while its server is active.
