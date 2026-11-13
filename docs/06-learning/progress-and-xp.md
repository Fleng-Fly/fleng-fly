# Progress and xp

Profile.xp is the total. ExerciseSubmission.xp_awarded prevents repeat points; retries update attempts without awarding twice. LessonProgress completes after all exercise states complete. Progress stores aggregate started/completed lessons, study minutes and last activity; /progress/me includes exercises, XP and per-published-course counts.

LearningActivity uses distinct server-policy days with LEARNING_TIMEZONE. Gamification derives streaks and threshold achievements. Leaderboard ranks all-time XP with stable ties and includes the caller's global rank beyond the top list; private account fields are omitted.

Profile.level defaults to 1 but automatic numeric advancement is absent. Flashcard study/completion awards no XP; test-words is a handoff, not a testing/grading subsystem. See [gamification API](../03-backend/gamification-api.md).

[Section index](README.md) · [Documentation home](../README.md)
