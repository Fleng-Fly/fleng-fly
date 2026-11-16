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
| leaderboard.html | leaderboard.js | All-time ranking and own position |

Course/lesson URLs use ?slug=. Public metadata is distinct from authenticated learning/private state. No standalone Vocabulary, Flashcards, Progress, Challenges, Practice, AI Tutor or reset-password page exists. The lesson Vocabulary tab contains personal saved words, not the shared course dictionary.

[Section index](README.md) · [Documentation home](../README.md)
