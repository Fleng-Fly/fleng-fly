# Grading

single_choice compares the submitted ID with correct_option_id exactly. Text comparison trims, casefolds and collapses whitespace for answer and accepted_answers. It does not infer synonyms, normalize NFC, assess essays or call AI. self_check records a learner's own assessment and is not objective grading.

Submission feedback reveals applicable correct/model answers and explanations. Authenticated learners can attempt a question to see feedback; answer-key exclusion before submission is not an exam secrecy guarantee. Malformed/empty submissions are rejected before grading.

Completion and once-only XP persist under learner locking. The validator probes the real grader with expected/wrong/empty answers, proving contract consistency rather than semantic correctness of the authored key.

[Section index](README.md) · [Documentation home](../README.md)

A self_check attempt completes the exercise even when selfAssessment=incorrect, and can therefore award its once-only points. isCorrect records the assessment while completed records participation. Study minutes are credited from lesson.estimated_minutes upon first lesson completion, not measured browser time. Empty lessons do not auto-complete.
