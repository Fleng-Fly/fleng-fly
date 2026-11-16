# Module dependencies

The aggregator imports health, auth, users, progress, catalog, exercises, vocabulary, gamification, password_reset and ai routers. get_current_user decodes JWT then loads persisted identity/profile; it never creates users.

Auth uses shared limits and user conversion. Exercises use catalog visibility, learner locking and gamification hooks. Progress reads lesson/exercise state plus published courses. Vocabulary owns review scheduling and flashcard snapshots. Gamification owns activity/streak/achievement/leaderboard rules. AI uses bounded published content and learner context; recommendations do not require a provider.

The importer reuses Course/Lesson/Exercise/CourseVocabularyItem. Offline validation reuses its contract and real objective grader. Preview wrappers explicitly allow draft service reads after reviewer authorization. [Project map](../../project-map/modules.md) retains implementation history; [schema](../05-database/schema.md) shows persisted dependencies.

[Section index](README.md) · [Documentation home](../README.md)
