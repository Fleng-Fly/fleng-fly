# Vocabulary

My Words are user-owned VocabularyItem rows: word, translation, example, optional lesson link, learned and due_at. APIs scope reads/writes/history to the caller, support due/lesson filters and bounded pagination. Uniqueness is per user; insertion normalizes words. Lesson association requires visible content.

Course Words are shared CourseVocabularyItem rows linked to a published course, inheriting its level. courseId/level filters do not populate personal words. Curriculum import never automatically fills My Words.

Reviews append history and schedule 1-day retry or 7-day remembered intervals. Direct learned updates schedule seven days or immediate due. No adaptive SRS is implemented. Existing lesson UI manages personal saved words; dedicated vocabulary management remains future work.

[Section index](README.md) · [Documentation home](../README.md)
