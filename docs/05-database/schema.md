# Database schema

Derived from [SQLAlchemy models](../../backend/app/db/models.py). Alembic remains upgrade authority. Ownership also requires service filters; child entities inherit ownership from parents. See [responsibilities/relationships](relationships.md) and [integrity](data-integrity.md).

## AIConversation

Table: `ai_conversations`.

| Column | Type | Nullable | Key/reference |
| --- | --- | --- | --- |
| id | CHAR(32) | False | PK |
| user_id | CHAR(32) | False | FK users.id |
| model | VARCHAR(200) | False | — |
| created_at | DATETIME | False | — |

Constraints/indexes beyond primary/foreign keys:

- Index `ix_ai_conversations_user_id` on `user_id`; unique=False

## AIMessage

Table: `ai_messages`.

| Column | Type | Nullable | Key/reference |
| --- | --- | --- | --- |
| id | CHAR(32) | False | PK |
| conversation_id | CHAR(32) | False | FK ai_conversations.id |
| role | VARCHAR(20) | False | — |
| content | TEXT | False | — |
| model | VARCHAR(200) | False | — |
| usage | JSON | True | — |
| created_at | DATETIME | False | — |

Constraints/indexes beyond primary/foreign keys:

- `ai_message_role_check` (CheckConstraint): `role IN ('user', 'assistant')`
- Index `ix_ai_messages_conversation_id` on `conversation_id`; unique=False

## AIUsage

Table: `ai_usage`.

| Column | Type | Nullable | Key/reference |
| --- | --- | --- | --- |
| request_id | CHAR(32) | True | — |
| id | CHAR(32) | False | PK |
| user_id | CHAR(32) | False | FK users.id |
| model | VARCHAR(200) | False | — |
| status | VARCHAR(20) | False | — |
| reserved_tokens | INTEGER | False | — |
| usage | JSON | True | — |
| created_at | DATETIME | False | — |

Constraints/indexes beyond primary/foreign keys:

- Index `ai_usage_request_key` on `user_id, request_id`; unique=True
- Index `ix_ai_usage_user_id` on `user_id`; unique=False

## Achievement

Table: `achievements`.

| Column | Type | Nullable | Key/reference |
| --- | --- | --- | --- |
| code | VARCHAR(40) | False | PK |
| title | VARCHAR(100) | False | — |
| metric | VARCHAR(30) | False | — |
| threshold | INTEGER | False | — |

Constraints/indexes beyond primary/foreign keys:

None declared beyond keys.

## Course

Table: `courses`.

| Column | Type | Nullable | Key/reference |
| --- | --- | --- | --- |
| id | CHAR(32) | False | PK |
| slug | VARCHAR | False | UNIQUE |
| title | VARCHAR | False | — |
| description | TEXT | False | — |
| level | VARCHAR(2) | False | — |
| position | INTEGER | False | — |
| is_published | BOOLEAN | False | — |
| created_at | DATETIME | False | — |
| updated_at | DATETIME | False | — |

Constraints/indexes beyond primary/foreign keys:

- `courses_level_check` (CheckConstraint): `level IN ('A0', 'A1', 'A2', 'B1', 'B2', 'C1', 'C2')`
- `unnamed` (UniqueConstraint): `slug`

## CourseVocabularyItem

Table: `course_vocabulary_items`.

| Column | Type | Nullable | Key/reference |
| --- | --- | --- | --- |
| id | CHAR(32) | False | PK |
| course_id | CHAR(32) | False | FK courses.id |
| word | VARCHAR(120) | False | — |
| translation | VARCHAR(300) | False | — |
| example | VARCHAR(1000) | False | — |

Constraints/indexes beyond primary/foreign keys:

- `course_vocabulary_word_key` (UniqueConstraint): `course_id, word`
- Index `ix_course_vocabulary_items_course_id` on `course_id`; unique=False

## Exercise

Table: `exercises`.

| Column | Type | Nullable | Key/reference |
| --- | --- | --- | --- |
| id | CHAR(32) | False | PK |
| lesson_id | CHAR(32) | False | FK lessons.id |
| slug | VARCHAR | False | UNIQUE |
| position | INTEGER | False | — |
| type | VARCHAR(20) | False | — |
| prompt | TEXT | False | — |
| points | INTEGER | False | — |
| options | JSON | True | — |
| correct_option_id | VARCHAR(64) | True | — |
| accepted_answers | JSON | True | — |
| model_answer | TEXT | True | — |
| explanation | TEXT | True | — |
| created_at | DATETIME | False | — |
| updated_at | DATETIME | False | — |

Constraints/indexes beyond primary/foreign keys:

- `unnamed` (UniqueConstraint): `slug`
- `exercises_type_check` (CheckConstraint): `type IN ('single_choice', 'text', 'self_check')`
- Index `ix_exercises_lesson_id` on `lesson_id`; unique=False

## ExerciseSubmission

Table: `exercise_submissions`.

| Column | Type | Nullable | Key/reference |
| --- | --- | --- | --- |
| id | CHAR(32) | False | PK |
| user_id | CHAR(32) | False | FK users.id |
| exercise_id | CHAR(32) | False | FK exercises.id |
| answer | TEXT | True | — |
| is_correct | BOOLEAN | True | — |
| completed | BOOLEAN | False | — |
| xp_awarded | BOOLEAN | False | — |
| attempts | INTEGER | False | — |
| submitted_at | DATETIME | False | — |
| updated_at | DATETIME | False | — |

Constraints/indexes beyond primary/foreign keys:

- `exercise_submissions_user_exercise_key` (UniqueConstraint): `user_id, exercise_id`
- Index `ix_exercise_submissions_user_id` on `user_id`; unique=False
- Index `ix_exercise_submissions_exercise_id` on `exercise_id`; unique=False

## FlashcardSession

Table: `vocabulary_flashcard_sessions`.

| Column | Type | Nullable | Key/reference |
| --- | --- | --- | --- |
| id | CHAR(32) | False | PK |
| user_id | CHAR(32) | False | FK users.id |
| source | VARCHAR(20) | False | — |
| status | VARCHAR(20) | False | — |
| cards | JSON | False | — |
| created_at | DATETIME | False | — |
| completed_at | DATETIME | True | — |

Constraints/indexes beyond primary/foreign keys:

- `flashcard_source_check` (CheckConstraint): `source IN ('my_words', 'course_words')`
- `flashcard_status_check` (CheckConstraint): `status IN ('active', 'completed', 'empty')`
- Index `ix_vocabulary_flashcard_sessions_user_id` on `user_id`; unique=False

## LearningActivity

Table: `learning_activity`.

| Column | Type | Nullable | Key/reference |
| --- | --- | --- | --- |
| id | CHAR(32) | False | PK |
| user_id | CHAR(32) | False | FK users.id |
| day | DATE | False | — |

Constraints/indexes beyond primary/foreign keys:

- `activity_user_day_key` (UniqueConstraint): `user_id, day`
- Index `ix_learning_activity_user_id` on `user_id`; unique=False

## Lesson

Table: `lessons`.

| Column | Type | Nullable | Key/reference |
| --- | --- | --- | --- |
| id | CHAR(32) | False | PK |
| course_id | CHAR(32) | False | FK courses.id |
| slug | VARCHAR | False | UNIQUE |
| title | VARCHAR | False | — |
| summary | VARCHAR | False | — |
| theory | TEXT | False | — |
| position | INTEGER | False | — |
| estimated_minutes | INTEGER | False | — |
| is_published | BOOLEAN | False | — |
| created_at | DATETIME | False | — |
| updated_at | DATETIME | False | — |

Constraints/indexes beyond primary/foreign keys:

- `unnamed` (UniqueConstraint): `slug`
- Index `ix_lessons_course_id` on `course_id`; unique=False

## LessonProgress

Table: `lesson_progress`.

| Column | Type | Nullable | Key/reference |
| --- | --- | --- | --- |
| id | CHAR(32) | False | PK |
| user_id | CHAR(32) | False | FK users.id |
| lesson_id | CHAR(32) | False | FK lessons.id |
| status | VARCHAR(20) | False | — |
| started_at | DATETIME | False | — |
| completed_at | DATETIME | True | — |
| updated_at | DATETIME | False | — |

Constraints/indexes beyond primary/foreign keys:

- `lesson_progress_user_lesson_key` (UniqueConstraint): `user_id, lesson_id`
- `lesson_progress_status_check` (CheckConstraint): `status IN ('in_progress', 'completed')`
- Index `ix_lesson_progress_lesson_id` on `lesson_id`; unique=False
- Index `ix_lesson_progress_user_id` on `user_id`; unique=False

## PasswordReset

Table: `password_resets`.

| Column | Type | Nullable | Key/reference |
| --- | --- | --- | --- |
| id | CHAR(32) | False | PK |
| user_id | CHAR(32) | False | FK users.id |
| token_hash | VARCHAR(64) | False | UNIQUE |
| expires_at | DATETIME | False | — |
| used_at | DATETIME | True | — |

Constraints/indexes beyond primary/foreign keys:

- `unnamed` (UniqueConstraint): `token_hash`
- Index `ix_password_resets_user_id` on `user_id`; unique=False

## Profile

Table: `profiles`.

| Column | Type | Nullable | Key/reference |
| --- | --- | --- | --- |
| id | CHAR(32) | False | PK |
| user_id | CHAR(32) | False | UNIQUE, FK users.id |
| display_name | VARCHAR | False | — |
| english_level | VARCHAR(2) | False | — |
| preferred_language | VARCHAR(40) | False | — |
| level | INTEGER | False | — |
| xp | INTEGER | False | — |
| created_at | DATETIME | False | — |
| updated_at | DATETIME | False | — |

Constraints/indexes beyond primary/foreign keys:

- `unnamed` (UniqueConstraint): `user_id`

## Progress

Table: `progress`.

| Column | Type | Nullable | Key/reference |
| --- | --- | --- | --- |
| id | CHAR(32) | False | PK |
| user_id | CHAR(32) | False | UNIQUE, FK users.id |
| lessons_started | INTEGER | False | — |
| lessons_completed | INTEGER | False | — |
| study_minutes | INTEGER | False | — |
| last_activity_at | DATETIME | True | — |
| created_at | DATETIME | False | — |
| updated_at | DATETIME | False | — |

Constraints/indexes beyond primary/foreign keys:

- `unnamed` (UniqueConstraint): `user_id`

## RefreshToken

Table: `refresh_tokens`.

| Column | Type | Nullable | Key/reference |
| --- | --- | --- | --- |
| id | CHAR(32) | False | PK |
| user_id | CHAR(32) | False | FK users.id |
| token_hash | VARCHAR(64) | False | UNIQUE |
| expires_at | DATETIME | False | — |
| revoked_at | DATETIME | True | — |
| replaced_by_id | CHAR(32) | True | FK refresh_tokens.id |
| created_at | DATETIME | False | — |

Constraints/indexes beyond primary/foreign keys:

- `unnamed` (UniqueConstraint): `token_hash`
- Index `ix_refresh_tokens_user_id` on `user_id`; unique=False

## RequestLimit

Table: `request_limits`.

| Column | Type | Nullable | Key/reference |
| --- | --- | --- | --- |
| key | VARCHAR(100) | False | PK |
| window | DATETIME | False | PK |
| count | INTEGER | False | — |

Constraints/indexes beyond primary/foreign keys:

None declared beyond keys.

## User

Table: `users`.

| Column | Type | Nullable | Key/reference |
| --- | --- | --- | --- |
| id | CHAR(32) | False | PK |
| email | VARCHAR | False | UNIQUE |
| password_hash | VARCHAR | False | — |
| created_at | DATETIME | False | — |
| updated_at | DATETIME | False | — |

Constraints/indexes beyond primary/foreign keys:

- `unnamed` (UniqueConstraint): `email`

## UserAchievement

Table: `user_achievements`.

| Column | Type | Nullable | Key/reference |
| --- | --- | --- | --- |
| user_id | CHAR(32) | False | PK, FK users.id |
| achievement_code | VARCHAR(40) | False | PK, FK achievements.code |
| awarded_at | DATETIME | False | — |

Constraints/indexes beyond primary/foreign keys:

None declared beyond keys.

## VocabularyItem

Table: `vocabulary_items`.

| Column | Type | Nullable | Key/reference |
| --- | --- | --- | --- |
| id | CHAR(32) | False | PK |
| user_id | CHAR(32) | False | FK users.id |
| lesson_id | CHAR(32) | True | FK lessons.id |
| word | VARCHAR(120) | False | — |
| translation | VARCHAR(300) | False | — |
| example | VARCHAR(1000) | False | — |
| learned | BOOLEAN | False | — |
| due_at | DATETIME | False | — |
| created_at | DATETIME | False | — |

Constraints/indexes beyond primary/foreign keys:

- `vocabulary_user_word_key` (UniqueConstraint): `user_id, word`
- Index `ix_vocabulary_items_user_id` on `user_id`; unique=False

## VocabularyReview

Table: `vocabulary_reviews`.

| Column | Type | Nullable | Key/reference |
| --- | --- | --- | --- |
| id | CHAR(32) | False | PK |
| item_id | CHAR(32) | False | FK vocabulary_items.id |
| remembered | BOOLEAN | False | — |
| created_at | DATETIME | False | — |

Constraints/indexes beyond primary/foreign keys:

- Index `ix_vocabulary_reviews_item_id` on `item_id`; unique=False
