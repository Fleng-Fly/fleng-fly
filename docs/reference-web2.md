# Reference-board completion — website 2026.11.16-web.2

This release starts from actual GitHub main ba6a4ec, retaining the newer Render
storage/PostgreSQL initialization and persistent AI usage/budget controls. The
Windows updater path/exit-code correction is retained too. It contains only the
existing FastAPI + plain HTML/CSS/JavaScript website; no app shell/runtime/EXE,
install buttons, manifest links or new worker registration.

## Comparison with the supplied board

| Board screen | State in this release |
| --- | --- |
| Dashboard, lesson player, Settings, login/register, leaderboard | Existing pages retained with the purple theme |
| My Words | Existing search/add/filters and four practice modes retained |
| Course Words | Added a dedicated library: courses/levels, search, sorting, selection and saving favourites |
| Standalone study card screens | Added Study & Test, real owned snapshot sets, previous/next, 3D reveal, sound speed and focus view/Escape |
| Vocabulary multiple choice / missing letters | Added a standalone handoff from completed cards, plus Write the word |
| Test completion card | Added current-run metrics, actual word outcomes, time, replay and mistakes-only retry |
| Our Team profile cards | Added public repository contributors with initials/profile links, keeping role-area cards below |
| Typography/palette and decoration | Existing Poppins/purple tokens retained; new responsive cards and reduced-motion-aware effects added |

The raster is a small overview, so unreadable controls are not invented. Empty
rectangles on the left are treated as card-player layouts. This update does not
claim to add video recording, microphone grading or an external audio-lesson
library. Existing lesson tabs remain Theory/Practice/Vocabulary, preserving the
current main navigation rather than restoring the obsolete duplicate Test tab.

## Data and behavior

Course Words uses the existing published-course and course-vocabulary APIs with
100-row pagination. Level/course/query filters combine; selection is capped at
50. The session builder supports 1–50 words and optional mixed selection. Save
calls the existing personal vocabulary API, handling already-saved words.

Flashcard creation accepts optional limit (1–50, default 10) and wordIds (1–50
UUIDs, no duplicates). Every ID is checked against the caller-owned or published
course query and all supplied filters before a session is stored. Explicit order
is retained. Existing requests still select ten deterministic cards by default.
No schema migration was introduced by these additions.

The card player reloads the existing server-owned snapshot by URL ID. Reveal
unlocks Next; final navigation acknowledges completion and reads /test-words
before testing. Personal answers call the existing review endpoint and count
only successful saves. Course recall answers are low-stakes browser practice:
results are for that run only and earn no XP or automatic mastery. They do not
pretend to be stored course progress. Persisted card composition survives refresh;
current card index and in-progress test answers reset when leaving the page.

Contributor handles devid-wp and maybelynux were verified on 2026-11-16 through
https://api.github.com/repos/Fleng-Fly/fleng-fly/contributors . No real names,
portraits, specializations, employment claims or social accounts were invented.
The profile links point to those public handles; there are no external avatar
requests from the visitor's browser.

## Validation and limits

- 46 Node VM/DOM behavior scenarios passed, including new selection, saving,
  completion failure/retry, test handoff, accurate summary/mistakes retry and
  failed personal review behavior. Existing navigation/AI scenarios retained.
- 26 targeted FastAPI/SQLite tests passed: development-draft compatibility,
  static frontend, flashcard ownership/
  persistence and new selected-word authorization/publication/bounds cases.
- Worker retirement and install-removal checks passed across all HTML pages.
- Ruff and focused mypy passed for changed Python code; JS syntax, page/asset
  references, documented contracts and archive/patch checks are release checks.
- Chrome desktop visual/interaction QA used an isolated static fixture build
  with fictional account data and real curriculum text. The production API and
  authentication files were not replaced. Fixture code is excluded from release.
  Selection/save, two-way cards, test handoff, wrong/right answers, 50% summary,
  mistakes-only retry and focus/Escape were exercised. Separate real backend
  ownership/write tests and an isolated real SQLite startup also passed.
- 390px iframe viewports checked Course Words, Our Team and Study setup with no
  horizontal overflow; this is responsive-layout QA, not a physical phone test.
- No real-user browser sign-in, Windows GUI/script execution, hardware speech
  playback, PostgreSQL integration or live host deployment was tested here.

Independent review checked ownership/publication, private-word isolation, failed
save handling, no invented XP and no reinstall path. The focus control now stays
disabled until its handler is attached. Existing main AI/storage safeguards are
kept; no original database migration was rewritten.

## Use and publish

The full source archive opens with START-WINDOWS.cmd → http://localhost:3001
(Python 3.11+ and Node.js 20+ required). Use the new sidebar entries Course Words
and Study & Test. Existing users/configuration/databases are not included in the
archive and should stay in their current backend data directory.

For GitHub publication, scripts/UPDATE-SITE.cmd uses adjacent update-website.ps1
and website.patch. It updates the existing C:\Users\Roman\Fleng-GitHub checkout,
refuses tracked local changes, fast-forwards main, validates the patch and pushes
without force after committing the prepared update. The package targets the
recorded main base. Conflicts stop rather than overwriting newer user changes.
After a successful push, deploy the existing Render/Netlify services and check
/version.json for 2026.11.16-web.2. No remote publication is claimed by this ZIP.
