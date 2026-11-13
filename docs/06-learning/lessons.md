# Lessons

Lesson belongs to Course and has globally unique slug, summary, theory, position, estimated_minutes and publication flag. Both lesson and course must be published for ordinary reads. Public detail omits answer keys.

Theory uses blank-line blocks, ## headings and - lists rendered with safe DOM nodes. Theory, Practice, Test and Vocabulary are existing UI views; Practice/Test reuse the same exercise list rather than separate locked exams. Start/resume is idempotent and completion is server-derived from exercise states.

Draft JSON includes goals, grammar, examples, readings and prerequisites, but these are not all independent database columns. Prerequisites are editorial metadata, not enforced access locks. Lesson-to-lesson navigation uses the course list.

[Section index](README.md) · [Documentation home](../README.md)
