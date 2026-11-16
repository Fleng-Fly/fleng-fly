# Lessons

Lesson belongs to Course and has globally unique slug, summary, theory, position, estimated_minutes and publication flag. Both lesson and course must be published for ordinary reads. Public detail omits answer keys.

Theory uses blank-line blocks, ## headings and - lists rendered with safe DOM nodes. Theory, Practice and Vocabulary are the lesson views. Theory opens by default; valid `?tab=practice` and `?tab=vocabulary` links select those views, while obsolete `?tab=test` falls back to Theory. Practice retains the existing graded exercises and XP. Start/resume is idempotent and completion is server-derived from exercise states.

Draft JSON includes goals, grammar, examples, readings and prerequisites, but these are not all independent database columns. Prerequisites are editorial metadata, not enforced access locks. Lesson-to-lesson navigation uses the course list.

[Section index](README.md) · [Documentation home](../README.md)
