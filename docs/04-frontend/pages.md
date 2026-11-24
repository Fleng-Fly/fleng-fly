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
| vocabulary.html | vocabulary.js | Personal words and Mixed Practice |
| course-words.html | course-words.js | Published course vocabulary, course/search filters, save and practise |
| leaderboard.html | leaderboard.js | All-time ranking and own position |

Course/lesson URLs use ?slug=. Public metadata is distinct from authenticated learning/private state. Personal vocabulary and Mixed Practice share vocabulary.html. Course Words uses course-words.html. Progress, Challenges and a standalone AI Tutor remain deferred. The password-reset page is reset-password.html. The lesson Vocabulary tab contains personal saved words, not the shared course dictionary.

Lesson and vocabulary practice check a selected answer or completed letter tiles
immediately. Typed answers are checked after 1.5 seconds without input or when
the learner presses Enter. Self-assessed exercises use the learner's rating.

[Section index](README.md) · [Documentation home](../README.md)

Placement Test MVP uses `/placement-test.html`, `js/placement-test.js` and
`js/placement-api.js`, with its own scoped stylesheet. It is deliberately not wired
into Dashboard/sidebar in this stage. [Methodology and limitations](../placement-test.md).


Words is a native sidebar disclosure with My Words and Course Words links. It
opens on vocabulary/practice pages and marks the current child with aria-current.
Practice stays inside My Words; Course Words saves through the existing vocabulary
API and can open the saved word in that same practice engine. No sidebar counters
or client-invented learning totals are shown.

Course Words searches English words and Ukrainian translations as the learner
types, including separate translation variants and partial matches. Exact
matches rank first across the paginated catalog. Clearing the search restores
the initial order within the current course and lesson filters.
The Tests button above the filters opens Mixed Practice in My Words.

Start Practice creates one task per selected personal word and balances four
formats subject to word eligibility. Mistakes show the answer and rejoin the
queue tail in the same format. Success removes the task and advances. The
current tab stores queue, scores, and pending review ID per learner, so reload
resumes the practice without resending a distinct review. Old practice URLs
open Mixed Practice and retain their optional starting word. A review updates
the existing schedule and contributes no XP.
