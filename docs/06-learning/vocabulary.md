# Vocabulary

My Words are user-owned VocabularyItem rows: word, translation, example, optional lesson link, learned and due_at. APIs scope reads/writes/history to the caller, support due/lesson filters and bounded pagination. Uniqueness is per user; insertion normalizes words. Lesson association requires visible content.

Course Words are shared CourseVocabularyItem rows linked to a published course,
inheriting its level. Learners can browse them by course or level.

Each of the five A0–B2 curriculum courses has 200 words and expressions, with 20
per lesson. The vocabulary tab lists the lesson's words. Practice includes ten
additional multiple-choice questions per lesson, alternating between English
and Ukrainian prompts. Completing a lesson collects its words in My Words.
Previously completed lessons collect newly added words when the learner opens
the dictionary.

Reviews append history and schedule 1-day retry or 7-day remembered intervals.
Direct learned updates schedule seven days or immediate due. Learners can manage
and practise their saved vocabulary in My Words.

[Section index](README.md) · [Documentation home](../README.md)
