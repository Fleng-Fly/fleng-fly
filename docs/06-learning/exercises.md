# Exercises

Supported application types: single_choice, text, self_check. Public schemas expose ID/slug/order/type/prompt/points/options, excluding correct_option_id, accepted_answers, model_answer and explanation. Submission resolves the exercise within the visible lesson.

SubmissionRequest requires exerciseId, answer (max 2000 characters) and optional selfAssessment=correct/incorrect. Single choices require a valid option ID; text must be nonblank; self-check needs meaningful text and an assessment. Domain-invalid answers return 422 INVALID_ANSWER. The draft importer currently accepts only single_choice despite three application types.

One user/exercise row retains latest attempt and increments attempts. Completed state remains sticky on retry. Incorrect objective answers do not grant new XP. [Grading](grading.md) and [API](../03-backend/exercises-api.md) explain details.

[Section index](README.md) · [Documentation home](../README.md)
