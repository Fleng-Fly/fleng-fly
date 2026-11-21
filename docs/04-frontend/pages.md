# Pages

| HTML page | Main module | Responsibility |
| --- | --- | --- |
| index.html | home.js | Public landing |
| register.html | register.js | Create account |
| login.html | login.js | Sign in |
| dashboard.html | dashboard.js | Persisted learning metrics and courses |
| courses.html | courses.js | Catalog, level/search filters |
| course.html | course.js | Course and lesson list by slug |
| lesson.html | lesson.js | Theory, practice/test, progress, personal words |
| settings.html | settings.js | Profile/email/language/password |
| vocabulary.html | vocabulary.js | Personal words and four review/practice modes |
| course-words.html | course-words.js | Published course vocabulary, course/search filters, save and practise |
| leaderboard.html | leaderboard.js | All-time ranking and own position |
| reading.html | reading.js | Reading library: topic/level/status/saved filters, bookmarks, topic preferences |
| reading-article.html?slug= | reading-article.js | Article, throttled read progress, quiz with autosave, result review |

Course/lesson URLs use ?slug=. Public metadata is distinct from authenticated learning/private state. Personal vocabulary and its practice modes share vocabulary.html. Course Words uses course-words.html. Progress, Challenges and a standalone AI Tutor remain deferred. The password-reset page is reset-password.html. The lesson Vocabulary tab contains personal saved words, not the shared course dictionary.

[Section index](README.md) · [Documentation home](../README.md)

Placement Test MVP uses `/placement-test.html`, `js/placement-test.js` and
`js/placement-api.js`, with its own scoped stylesheet. It is deliberately not wired
into Dashboard/sidebar in this stage. [Methodology and limitations](../placement-test.md).


Words is a native sidebar disclosure with My Words and Course Words links. It
opens on vocabulary/practice pages and marks the current child with aria-current.
Practice stays inside My Words; Course Words saves through the existing vocabulary
API and can open the saved word in that same practice engine. No sidebar counters
or client-invented learning totals are shown.

## Reading

`reading.html` and `reading-article.html` use the shared workspace (sidebar link "Reading") and
`css/reading.css`, which reuses the Fleng tokens plus `lesson-button`/`lesson-option` from
`lesson.css`. Modules: `reading-ui.js` (level badge, bookmark toggle), `reading-quiz.js` (pure
helpers), `reading-sync.js` (rate-safe writer). Interface strings are the `rd.*` keys (EN/UK).

- **Throttling.** Progress and quiz answers go through `createWriter`: only the newest value is
  kept, requests never overlap, there is a quiet period plus a minimum interval (progress 5 s,
  at most 12 writes/min; answers 3 s, at most 20/min), failures retry with back-off and `429`
  pauses for a minute. The server limits are 60 and 30 per minute. Progress needs a user
  interaction and a short dwell time (a quarter of the reading time, 5-30 s) before it may reach
  100 %, so opening a short article never completes it; real reading-time accounting is separate
  future work (heartbeat / `study_minutes`).
- **Quiz.** Starting resumes an open attempt, answers autosave and are restored after a reload,
  Submit needs every question answered and sends the full set. The page holds no answer key
  before submit (the API does not send one); the result view shows score, XP, the correct answer
  and explanation per question. Repeated passes show "already earned XP".
- **States.** Loading, empty (no articles / no match with a clear-filters action), error with
  retry, missing article, bookmark and topic-save errors, success (saved, passed). Layout is
  checked at 360 px with no horizontal scroll.
- **Topics.** Preferred categories are starred and listed first; "My topics" merges the
  newest articles of up to 10 preferred categories (the API filters by one category).
