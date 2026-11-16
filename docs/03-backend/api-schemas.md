# API schema reference

Generated from runtime FastAPI OpenAPI. Required fields, aliases, nullability, defaults and validation bounds are exact schema declarations. `$ref` names refer to other named contracts on this page. Service rules may be stricter; consult endpoint notes. No private database records are used.

## AccessTokenResponse

```json
{
  "properties": {
    "accessToken": {
      "type": "string",
      "title": "Accesstoken"
    },
    "tokenType": {
      "type": "string",
      "title": "Tokentype",
      "default": "bearer"
    },
    "expiresIn": {
      "type": "integer",
      "title": "Expiresin"
    }
  },
  "type": "object",
  "required": [
    "accessToken",
    "expiresIn"
  ],
  "title": "AccessTokenResponse"
}
```

## AchievementResponse

```json
{
  "properties": {
    "code": {
      "type": "string",
      "title": "Code"
    },
    "title": {
      "type": "string",
      "title": "Title"
    },
    "awardedAt": {
      "anyOf": [
        {
          "type": "string",
          "format": "date-time"
        },
        {
          "type": "null"
        }
      ],
      "title": "Awardedat"
    }
  },
  "type": "object",
  "required": [
    "code",
    "title",
    "awardedAt"
  ],
  "title": "AchievementResponse"
}
```

## ChatRequest

```json
{
  "properties": {
    "message": {
      "type": "string",
      "maxLength": 16000,
      "minLength": 1,
      "title": "Message"
    },
    "conversationId": {
      "anyOf": [
        {
          "type": "string",
          "format": "uuid"
        },
        {
          "type": "null"
        }
      ],
      "title": "Conversationid"
    },
    "lessonId": {
      "anyOf": [
        {
          "type": "string",
          "format": "uuid"
        },
        {
          "type": "null"
        }
      ],
      "title": "Lessonid"
    },
    "correctGrammar": {
      "type": "boolean",
      "title": "Correctgrammar",
      "default": true
    },
    "exerciseId": {
      "anyOf": [
        {
          "type": "string",
          "format": "uuid"
        },
        {
          "type": "null"
        }
      ],
      "title": "Exerciseid"
    },
    "requestId": {
      "anyOf": [
        {
          "type": "string",
          "format": "uuid"
        },
        {
          "type": "null"
        }
      ],
      "title": "Requestid"
    }
  },
  "additionalProperties": false,
  "type": "object",
  "required": [
    "message"
  ],
  "title": "ChatRequest"
}
```

## ChatResponse

```json
{
  "properties": {
    "conversationId": {
      "type": "string",
      "format": "uuid",
      "title": "Conversationid"
    },
    "message": {
      "$ref": "#/components/schemas/MessageResponse"
    }
  },
  "type": "object",
  "required": [
    "conversationId",
    "message"
  ],
  "title": "ChatResponse"
}
```

## ConversationResponse

```json
{
  "properties": {
    "id": {
      "type": "string",
      "format": "uuid",
      "title": "Id"
    },
    "model": {
      "type": "string",
      "title": "Model"
    },
    "createdAt": {
      "type": "string",
      "format": "date-time",
      "title": "Createdat"
    }
  },
  "type": "object",
  "required": [
    "id",
    "model",
    "createdAt"
  ],
  "title": "ConversationResponse"
}
```

## CourseDetailResponse

```json
{
  "properties": {
    "id": {
      "type": "string",
      "format": "uuid",
      "title": "Id"
    },
    "slug": {
      "type": "string",
      "title": "Slug"
    },
    "title": {
      "type": "string",
      "title": "Title"
    },
    "description": {
      "type": "string",
      "title": "Description"
    },
    "level": {
      "type": "string",
      "enum": [
        "A0",
        "A1",
        "A2",
        "B1",
        "B2",
        "C1",
        "C2"
      ],
      "title": "Level"
    },
    "lessons": {
      "items": {
        "$ref": "#/components/schemas/LessonSummaryResponse"
      },
      "type": "array",
      "title": "Lessons"
    }
  },
  "type": "object",
  "required": [
    "id",
    "slug",
    "title",
    "description",
    "level",
    "lessons"
  ],
  "title": "CourseDetailResponse",
  "description": "A course with its published lessons."
}
```

## CourseProgressResponse

```json
{
  "properties": {
    "courseId": {
      "type": "string",
      "format": "uuid",
      "title": "Courseid"
    },
    "slug": {
      "type": "string",
      "title": "Slug"
    },
    "title": {
      "type": "string",
      "title": "Title"
    },
    "level": {
      "type": "string",
      "title": "Level"
    },
    "lessonsTotal": {
      "type": "integer",
      "title": "Lessonstotal"
    },
    "lessonsStarted": {
      "type": "integer",
      "title": "Lessonsstarted"
    },
    "lessonsCompleted": {
      "type": "integer",
      "title": "Lessonscompleted"
    }
  },
  "type": "object",
  "required": [
    "courseId",
    "slug",
    "title",
    "level",
    "lessonsTotal",
    "lessonsStarted",
    "lessonsCompleted"
  ],
  "title": "CourseProgressResponse",
  "description": "The caller's progress through one published course."
}
```

## CourseSummaryResponse

```json
{
  "properties": {
    "id": {
      "type": "string",
      "format": "uuid",
      "title": "Id"
    },
    "slug": {
      "type": "string",
      "title": "Slug"
    },
    "title": {
      "type": "string",
      "title": "Title"
    },
    "description": {
      "type": "string",
      "title": "Description"
    },
    "level": {
      "type": "string",
      "enum": [
        "A0",
        "A1",
        "A2",
        "B1",
        "B2",
        "C1",
        "C2"
      ],
      "title": "Level"
    },
    "lessonCount": {
      "type": "integer",
      "title": "Lessoncount"
    }
  },
  "type": "object",
  "required": [
    "id",
    "slug",
    "title",
    "description",
    "level",
    "lessonCount"
  ],
  "title": "CourseSummaryResponse",
  "description": "A course in the catalog list."
}
```

## CourseWordResponse

```json
{
  "properties": {
    "id": {
      "type": "string",
      "format": "uuid",
      "title": "Id"
    },
    "courseId": {
      "type": "string",
      "format": "uuid",
      "title": "Courseid"
    },
    "word": {
      "type": "string",
      "title": "Word"
    },
    "translation": {
      "type": "string",
      "title": "Translation"
    },
    "example": {
      "type": "string",
      "title": "Example"
    }
  },
  "type": "object",
  "required": [
    "id",
    "courseId",
    "word",
    "translation",
    "example"
  ],
  "title": "CourseWordResponse"
}
```

## ExerciseOptionResponse

```json
{
  "properties": {
    "id": {
      "type": "string",
      "title": "Id"
    },
    "text": {
      "type": "string",
      "title": "Text"
    }
  },
  "type": "object",
  "required": [
    "id",
    "text"
  ],
  "title": "ExerciseOptionResponse"
}
```

## ExercisePublicResponse

```json
{
  "properties": {
    "id": {
      "type": "string",
      "format": "uuid",
      "title": "Id"
    },
    "slug": {
      "type": "string",
      "title": "Slug"
    },
    "position": {
      "type": "integer",
      "title": "Position"
    },
    "type": {
      "type": "string",
      "title": "Type"
    },
    "prompt": {
      "type": "string",
      "title": "Prompt"
    },
    "points": {
      "type": "integer",
      "title": "Points"
    },
    "options": {
      "anyOf": [
        {
          "items": {
            "$ref": "#/components/schemas/ExerciseOptionResponse"
          },
          "type": "array"
        },
        {
          "type": "null"
        }
      ],
      "title": "Options"
    }
  },
  "type": "object",
  "required": [
    "id",
    "slug",
    "position",
    "type",
    "prompt",
    "points"
  ],
  "title": "ExercisePublicResponse",
  "description": "Public exercise content.\n\nDeliberately excludes every grading secret (`correct_option_id`,\n`accepted_answers`, `model_answer`, `explanation`). Options are only present\nfor `single_choice` exercises."
}
```

## ExplainRequest

```json
{
  "properties": {
    "exerciseId": {
      "anyOf": [
        {
          "type": "string",
          "format": "uuid"
        },
        {
          "type": "null"
        }
      ],
      "title": "Exerciseid"
    },
    "lessonId": {
      "anyOf": [
        {
          "type": "string",
          "format": "uuid"
        },
        {
          "type": "null"
        }
      ],
      "title": "Lessonid"
    },
    "studentAnswer": {
      "type": "string",
      "maxLength": 4000,
      "minLength": 1,
      "title": "Studentanswer"
    },
    "topic": {
      "type": "string",
      "maxLength": 200,
      "minLength": 1,
      "title": "Topic",
      "default": "English grammar"
    }
  },
  "additionalProperties": false,
  "type": "object",
  "required": [
    "studentAnswer"
  ],
  "title": "ExplainRequest"
}
```

## Explanation

```json
{
  "properties": {
    "explanation": {
      "type": "string",
      "maxLength": 4000,
      "minLength": 1,
      "title": "Explanation"
    },
    "correctExample": {
      "type": "string",
      "maxLength": 2000,
      "minLength": 1,
      "title": "Correctexample"
    },
    "rule": {
      "type": "string",
      "maxLength": 2000,
      "minLength": 1,
      "title": "Rule"
    },
    "hint": {
      "type": "string",
      "maxLength": 1000,
      "title": "Hint",
      "default": ""
    }
  },
  "additionalProperties": false,
  "type": "object",
  "required": [
    "explanation",
    "correctExample",
    "rule"
  ],
  "title": "Explanation"
}
```

## Flashcard

```json
{
  "properties": {
    "wordId": {
      "type": "string",
      "format": "uuid",
      "title": "Wordid"
    },
    "word": {
      "type": "string",
      "title": "Word"
    },
    "translation": {
      "type": "string",
      "title": "Translation"
    },
    "example": {
      "type": "string",
      "title": "Example"
    }
  },
  "type": "object",
  "required": [
    "wordId",
    "word",
    "translation",
    "example"
  ],
  "title": "Flashcard"
}
```

## FlashcardCreate

```json
{
  "properties": {
    "source": {
      "type": "string",
      "enum": [
        "my_words",
        "course_words"
      ],
      "title": "Source"
    },
    "courseId": {
      "anyOf": [
        {
          "type": "string",
          "format": "uuid"
        },
        {
          "type": "null"
        }
      ],
      "title": "Courseid"
    },
    "level": {
      "anyOf": [
        {
          "type": "string",
          "enum": [
            "A0",
            "A1",
            "A2",
            "B1",
            "B2",
            "C1",
            "C2"
          ]
        },
        {
          "type": "null"
        }
      ],
      "title": "Level"
    }
  },
  "additionalProperties": false,
  "type": "object",
  "required": [
    "source"
  ],
  "title": "FlashcardCreate"
}
```

## FlashcardResponse

```json
{
  "properties": {
    "sessionId": {
      "type": "string",
      "format": "uuid",
      "title": "Sessionid"
    },
    "source": {
      "type": "string",
      "enum": [
        "my_words",
        "course_words"
      ],
      "title": "Source"
    },
    "status": {
      "type": "string",
      "enum": [
        "active",
        "completed",
        "empty"
      ],
      "title": "Status"
    },
    "total": {
      "type": "integer",
      "title": "Total"
    },
    "cards": {
      "items": {
        "$ref": "#/components/schemas/Flashcard"
      },
      "type": "array",
      "title": "Cards"
    },
    "testReady": {
      "type": "boolean",
      "title": "Testready"
    }
  },
  "type": "object",
  "required": [
    "sessionId",
    "source",
    "status",
    "total",
    "cards",
    "testReady"
  ],
  "title": "FlashcardResponse"
}
```

## GenerateRequest

```json
{
  "properties": {
    "level": {
      "anyOf": [
        {
          "type": "string",
          "enum": [
            "A0",
            "A1",
            "A2",
            "B1",
            "B2",
            "C1",
            "C2"
          ]
        },
        {
          "type": "null"
        }
      ],
      "title": "Level"
    },
    "topic": {
      "type": "string",
      "maxLength": 200,
      "minLength": 1,
      "title": "Topic"
    },
    "difficulty": {
      "type": "string",
      "enum": [
        "easy",
        "medium",
        "hard"
      ],
      "title": "Difficulty",
      "default": "medium"
    },
    "exerciseType": {
      "type": "string",
      "enum": [
        "multiple_choice",
        "fill_blank",
        "sentence_correction"
      ],
      "title": "Exercisetype"
    }
  },
  "additionalProperties": false,
  "type": "object",
  "required": [
    "topic",
    "exerciseType"
  ],
  "title": "GenerateRequest"
}
```

## GeneratedExercise

```json
{
  "properties": {
    "type": {
      "type": "string",
      "enum": [
        "multiple_choice",
        "fill_blank",
        "sentence_correction"
      ],
      "title": "Type"
    },
    "prompt": {
      "type": "string",
      "maxLength": 2000,
      "minLength": 1,
      "title": "Prompt"
    },
    "options": {
      "items": {
        "type": "string"
      },
      "type": "array",
      "maxItems": 6,
      "title": "Options"
    },
    "answer": {
      "type": "string",
      "maxLength": 1000,
      "minLength": 1,
      "title": "Answer"
    },
    "explanation": {
      "type": "string",
      "maxLength": 2000,
      "minLength": 1,
      "title": "Explanation"
    },
    "practiceOnly": {
      "type": "boolean",
      "const": true,
      "title": "Practiceonly",
      "default": true
    }
  },
  "additionalProperties": false,
  "type": "object",
  "required": [
    "type",
    "prompt",
    "answer",
    "explanation"
  ],
  "title": "GeneratedExercise"
}
```

## HTTPValidationError

```json
{
  "properties": {
    "detail": {
      "items": {
        "$ref": "#/components/schemas/ValidationError"
      },
      "type": "array",
      "title": "Detail"
    }
  },
  "type": "object",
  "title": "HTTPValidationError"
}
```

## HealthResponse

```json
{
  "properties": {
    "status": {
      "type": "string",
      "const": "ok",
      "title": "Status",
      "default": "ok"
    },
    "service": {
      "type": "string",
      "const": "backend",
      "title": "Service",
      "default": "backend"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "title": "Timestamp"
    },
    "database": {
      "type": "string",
      "enum": [
        "up",
        "down"
      ],
      "title": "Database"
    }
  },
  "type": "object",
  "required": [
    "timestamp",
    "database"
  ],
  "title": "HealthResponse"
}
```

## LeaderboardEntry

```json
{
  "properties": {
    "rank": {
      "type": "integer",
      "title": "Rank"
    },
    "displayName": {
      "type": "string",
      "title": "Displayname"
    },
    "xp": {
      "type": "integer",
      "title": "Xp"
    },
    "lessonsCompleted": {
      "type": "integer",
      "title": "Lessonscompleted"
    },
    "streak": {
      "type": "integer",
      "title": "Streak"
    },
    "isCurrentUser": {
      "type": "boolean",
      "title": "Iscurrentuser"
    }
  },
  "type": "object",
  "required": [
    "rank",
    "displayName",
    "xp",
    "lessonsCompleted",
    "streak",
    "isCurrentUser"
  ],
  "title": "LeaderboardEntry"
}
```

## LeaderboardResponse

```json
{
  "properties": {
    "entries": {
      "items": {
        "$ref": "#/components/schemas/LeaderboardEntry"
      },
      "type": "array",
      "title": "Entries"
    },
    "currentUser": {
      "anyOf": [
        {
          "$ref": "#/components/schemas/LeaderboardEntry"
        },
        {
          "type": "null"
        }
      ]
    },
    "total": {
      "type": "integer",
      "title": "Total"
    }
  },
  "type": "object",
  "required": [
    "entries",
    "currentUser",
    "total"
  ],
  "title": "LeaderboardResponse"
}
```

## LessonDetailResponse

```json
{
  "properties": {
    "id": {
      "type": "string",
      "format": "uuid",
      "title": "Id"
    },
    "slug": {
      "type": "string",
      "title": "Slug"
    },
    "title": {
      "type": "string",
      "title": "Title"
    },
    "summary": {
      "type": "string",
      "title": "Summary"
    },
    "theory": {
      "type": "string",
      "title": "Theory"
    },
    "position": {
      "type": "integer",
      "title": "Position"
    },
    "estimatedMinutes": {
      "type": "integer",
      "title": "Estimatedminutes"
    },
    "courseSlug": {
      "type": "string",
      "title": "Courseslug"
    },
    "courseTitle": {
      "type": "string",
      "title": "Coursetitle"
    },
    "level": {
      "type": "string",
      "enum": [
        "A0",
        "A1",
        "A2",
        "B1",
        "B2",
        "C1",
        "C2"
      ],
      "title": "Level"
    },
    "exercises": {
      "items": {
        "$ref": "#/components/schemas/ExercisePublicResponse"
      },
      "type": "array",
      "title": "Exercises"
    }
  },
  "type": "object",
  "required": [
    "id",
    "slug",
    "title",
    "summary",
    "theory",
    "position",
    "estimatedMinutes",
    "courseSlug",
    "courseTitle",
    "level",
    "exercises"
  ],
  "title": "LessonDetailResponse",
  "description": "A single lesson with its course context, theory body and public exercises."
}
```

## LessonExerciseStateResponse

```json
{
  "properties": {
    "exerciseId": {
      "type": "string",
      "format": "uuid",
      "title": "Exerciseid"
    },
    "completed": {
      "type": "boolean",
      "title": "Completed"
    },
    "isCorrect": {
      "anyOf": [
        {
          "type": "boolean"
        },
        {
          "type": "null"
        }
      ],
      "title": "Iscorrect"
    },
    "attempts": {
      "type": "integer",
      "title": "Attempts"
    },
    "pointsAwarded": {
      "type": "integer",
      "title": "Pointsawarded"
    },
    "answer": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "title": "Answer"
    }
  },
  "type": "object",
  "required": [
    "exerciseId",
    "completed",
    "isCorrect",
    "attempts",
    "pointsAwarded"
  ],
  "title": "LessonExerciseStateResponse",
  "description": "The caller's state for one exercise within a lesson."
}
```

## LessonProgressResponse

```json
{
  "properties": {
    "lessonSlug": {
      "type": "string",
      "title": "Lessonslug"
    },
    "lessonTitle": {
      "type": "string",
      "title": "Lessontitle"
    },
    "status": {
      "type": "string",
      "title": "Status"
    },
    "completed": {
      "type": "boolean",
      "title": "Completed"
    },
    "startedAt": {
      "anyOf": [
        {
          "type": "string",
          "format": "date-time"
        },
        {
          "type": "null"
        }
      ],
      "title": "Startedat"
    },
    "completedAt": {
      "anyOf": [
        {
          "type": "string",
          "format": "date-time"
        },
        {
          "type": "null"
        }
      ],
      "title": "Completedat"
    },
    "exercisesTotal": {
      "type": "integer",
      "title": "Exercisestotal"
    },
    "exercisesCompleted": {
      "type": "integer",
      "title": "Exercisescompleted"
    },
    "xpEarned": {
      "type": "integer",
      "title": "Xpearned"
    },
    "exercises": {
      "items": {
        "$ref": "#/components/schemas/LessonExerciseStateResponse"
      },
      "type": "array",
      "title": "Exercises"
    }
  },
  "type": "object",
  "required": [
    "lessonSlug",
    "lessonTitle",
    "status",
    "completed",
    "startedAt",
    "completedAt",
    "exercisesTotal",
    "exercisesCompleted",
    "xpEarned",
    "exercises"
  ],
  "title": "LessonProgressResponse",
  "description": "The caller's progress through a lesson."
}
```

## LessonSummaryResponse

```json
{
  "properties": {
    "id": {
      "type": "string",
      "format": "uuid",
      "title": "Id"
    },
    "slug": {
      "type": "string",
      "title": "Slug"
    },
    "title": {
      "type": "string",
      "title": "Title"
    },
    "summary": {
      "type": "string",
      "title": "Summary"
    },
    "position": {
      "type": "integer",
      "title": "Position"
    },
    "estimatedMinutes": {
      "type": "integer",
      "title": "Estimatedminutes"
    }
  },
  "type": "object",
  "required": [
    "id",
    "slug",
    "title",
    "summary",
    "position",
    "estimatedMinutes"
  ],
  "title": "LessonSummaryResponse",
  "description": "A lesson inside a course detail response (no theory body)."
}
```

## LoginRequest

```json
{
  "properties": {
    "email": {
      "type": "string",
      "format": "email",
      "title": "Email"
    },
    "password": {
      "type": "string",
      "maxLength": 128,
      "minLength": 1,
      "title": "Password"
    }
  },
  "type": "object",
  "required": [
    "email",
    "password"
  ],
  "title": "LoginRequest"
}
```

## MessageResponse

```json
{
  "properties": {
    "id": {
      "type": "string",
      "format": "uuid",
      "title": "Id"
    },
    "role": {
      "type": "string",
      "title": "Role"
    },
    "content": {
      "type": "string",
      "title": "Content"
    },
    "model": {
      "type": "string",
      "title": "Model"
    },
    "usage": {
      "anyOf": [
        {
          "additionalProperties": true,
          "type": "object"
        },
        {
          "type": "null"
        }
      ],
      "title": "Usage"
    },
    "createdAt": {
      "type": "string",
      "format": "date-time",
      "title": "Createdat"
    }
  },
  "type": "object",
  "required": [
    "id",
    "role",
    "content",
    "model",
    "usage",
    "createdAt"
  ],
  "title": "MessageResponse"
}
```

## PasswordChange

```json
{
  "properties": {
    "currentPassword": {
      "type": "string",
      "maxLength": 128,
      "minLength": 1,
      "title": "Currentpassword"
    },
    "newPassword": {
      "type": "string",
      "maxLength": 128,
      "minLength": 8,
      "title": "Newpassword"
    }
  },
  "type": "object",
  "required": [
    "currentPassword",
    "newPassword"
  ],
  "title": "PasswordChange"
}
```

## ProfileUpdate

```json
{
  "properties": {
    "email": {
      "anyOf": [
        {
          "type": "string",
          "format": "email"
        },
        {
          "type": "null"
        }
      ],
      "title": "Email"
    },
    "displayName": {
      "anyOf": [
        {
          "type": "string",
          "maxLength": 80,
          "minLength": 1
        },
        {
          "type": "null"
        }
      ],
      "title": "Displayname"
    },
    "englishLevel": {
      "anyOf": [
        {
          "type": "string",
          "enum": [
            "A0",
            "A1",
            "A2",
            "B1",
            "B2",
            "C1",
            "C2"
          ]
        },
        {
          "type": "null"
        }
      ],
      "title": "Englishlevel"
    },
    "preferredLanguage": {
      "anyOf": [
        {
          "type": "string",
          "maxLength": 40,
          "minLength": 1
        },
        {
          "type": "null"
        }
      ],
      "title": "Preferredlanguage"
    }
  },
  "type": "object",
  "title": "ProfileUpdate"
}
```

## ProgressResponse

```json
{
  "properties": {
    "userId": {
      "type": "string",
      "format": "uuid",
      "title": "Userid"
    },
    "lessonsStarted": {
      "type": "integer",
      "title": "Lessonsstarted"
    },
    "lessonsCompleted": {
      "type": "integer",
      "title": "Lessonscompleted"
    },
    "exercisesCompleted": {
      "type": "integer",
      "title": "Exercisescompleted"
    },
    "studyMinutes": {
      "type": "integer",
      "title": "Studyminutes"
    },
    "xp": {
      "type": "integer",
      "title": "Xp"
    },
    "lastActivityAt": {
      "anyOf": [
        {
          "type": "string",
          "format": "date-time"
        },
        {
          "type": "null"
        }
      ],
      "title": "Lastactivityat"
    },
    "updatedAt": {
      "anyOf": [
        {
          "type": "string",
          "format": "date-time"
        },
        {
          "type": "null"
        }
      ],
      "title": "Updatedat"
    },
    "courses": {
      "items": {
        "$ref": "#/components/schemas/CourseProgressResponse"
      },
      "type": "array",
      "title": "Courses"
    }
  },
  "type": "object",
  "required": [
    "userId",
    "lessonsStarted",
    "lessonsCompleted",
    "exercisesCompleted",
    "studyMinutes",
    "xp",
    "lastActivityAt",
    "updatedAt",
    "courses"
  ],
  "title": "ProgressResponse",
  "description": "Aggregate progress plus a per-course breakdown.\n\nNew fields are additive: existing clients that read only `lessonsStarted`,\n`lessonsCompleted`, `studyMinutes`, `lastActivityAt`, `updatedAt` and\n`userId` keep working."
}
```

## RegisterRequest

```json
{
  "properties": {
    "email": {
      "type": "string",
      "format": "email",
      "title": "Email"
    },
    "password": {
      "type": "string",
      "maxLength": 128,
      "minLength": 8,
      "title": "Password"
    },
    "displayName": {
      "type": "string",
      "maxLength": 80,
      "minLength": 1,
      "title": "Displayname"
    }
  },
  "type": "object",
  "required": [
    "email",
    "password",
    "displayName"
  ],
  "title": "RegisterRequest"
}
```

## ResetConfirm

```json
{
  "properties": {
    "token": {
      "type": "string",
      "maxLength": 200,
      "minLength": 32,
      "title": "Token"
    },
    "password": {
      "type": "string",
      "maxLength": 128,
      "minLength": 8,
      "title": "Password"
    }
  },
  "type": "object",
  "required": [
    "token",
    "password"
  ],
  "title": "ResetConfirm"
}
```

## ResetRequest

```json
{
  "properties": {
    "email": {
      "type": "string",
      "maxLength": 254,
      "format": "email",
      "title": "Email"
    }
  },
  "type": "object",
  "required": [
    "email"
  ],
  "title": "ResetRequest"
}
```

## ResetResponse

```json
{
  "properties": {
    "message": {
      "type": "string",
      "title": "Message",
      "default": "If the account exists, password reset instructions will be sent."
    }
  },
  "type": "object",
  "title": "ResetResponse"
}
```

## ReviewRequest

```json
{
  "properties": {
    "remembered": {
      "type": "boolean",
      "title": "Remembered"
    }
  },
  "type": "object",
  "required": [
    "remembered"
  ],
  "title": "ReviewRequest"
}
```

## ReviewResponse

```json
{
  "properties": {
    "id": {
      "type": "string",
      "format": "uuid",
      "title": "Id"
    },
    "remembered": {
      "type": "boolean",
      "title": "Remembered"
    },
    "createdAt": {
      "type": "string",
      "format": "date-time",
      "title": "Createdat"
    }
  },
  "type": "object",
  "required": [
    "id",
    "remembered",
    "createdAt"
  ],
  "title": "ReviewResponse"
}
```

## StreakResponse

```json
{
  "properties": {
    "current": {
      "type": "integer",
      "title": "Current"
    },
    "longest": {
      "type": "integer",
      "title": "Longest"
    },
    "lastActivityDate": {
      "anyOf": [
        {
          "type": "string",
          "format": "date"
        },
        {
          "type": "null"
        }
      ],
      "title": "Lastactivitydate"
    },
    "timezone": {
      "type": "string",
      "title": "Timezone"
    }
  },
  "type": "object",
  "required": [
    "current",
    "longest",
    "lastActivityDate",
    "timezone"
  ],
  "title": "StreakResponse"
}
```

## SubmissionRequest

```json
{
  "properties": {
    "exerciseId": {
      "type": "string",
      "format": "uuid",
      "title": "Exerciseid"
    },
    "answer": {
      "type": "string",
      "maxLength": 2000,
      "title": "Answer"
    },
    "selfAssessment": {
      "anyOf": [
        {
          "type": "string",
          "enum": [
            "correct",
            "incorrect"
          ]
        },
        {
          "type": "null"
        }
      ],
      "title": "Selfassessment"
    }
  },
  "type": "object",
  "required": [
    "exerciseId",
    "answer"
  ],
  "title": "SubmissionRequest"
}
```

## SubmissionResultResponse

```json
{
  "properties": {
    "exerciseId": {
      "type": "string",
      "format": "uuid",
      "title": "Exerciseid"
    },
    "type": {
      "type": "string",
      "title": "Type"
    },
    "isCorrect": {
      "anyOf": [
        {
          "type": "boolean"
        },
        {
          "type": "null"
        }
      ],
      "title": "Iscorrect"
    },
    "completed": {
      "type": "boolean",
      "title": "Completed"
    },
    "points": {
      "type": "integer",
      "title": "Points"
    },
    "xpAwarded": {
      "type": "integer",
      "title": "Xpawarded"
    },
    "feedback": {
      "type": "string",
      "title": "Feedback"
    },
    "correctOptionId": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "title": "Correctoptionid"
    },
    "acceptedAnswers": {
      "anyOf": [
        {
          "items": {
            "type": "string"
          },
          "type": "array"
        },
        {
          "type": "null"
        }
      ],
      "title": "Acceptedanswers"
    },
    "modelAnswer": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "title": "Modelanswer"
    },
    "explanation": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "title": "Explanation"
    },
    "lesson": {
      "$ref": "#/components/schemas/LessonProgressResponse"
    }
  },
  "type": "object",
  "required": [
    "exerciseId",
    "type",
    "isCorrect",
    "completed",
    "points",
    "xpAwarded",
    "feedback",
    "lesson"
  ],
  "title": "SubmissionResultResponse",
  "description": "The result of one graded submission.\n\nThe correct answer / model answer / explanation are revealed here (and only\nhere) so the learner can review the attempt."
}
```

## TokenResponse

```json
{
  "properties": {
    "accessToken": {
      "type": "string",
      "title": "Accesstoken"
    },
    "tokenType": {
      "type": "string",
      "title": "Tokentype",
      "default": "bearer"
    },
    "expiresIn": {
      "type": "integer",
      "title": "Expiresin"
    },
    "user": {
      "$ref": "#/components/schemas/UserResponse"
    }
  },
  "type": "object",
  "required": [
    "accessToken",
    "expiresIn",
    "user"
  ],
  "title": "TokenResponse"
}
```

## UserResponse

```json
{
  "properties": {
    "id": {
      "type": "string",
      "format": "uuid",
      "title": "Id"
    },
    "email": {
      "type": "string",
      "title": "Email"
    },
    "displayName": {
      "type": "string",
      "title": "Displayname"
    },
    "level": {
      "type": "integer",
      "title": "Level"
    },
    "xp": {
      "type": "integer",
      "title": "Xp"
    },
    "englishLevel": {
      "type": "string",
      "title": "Englishlevel",
      "default": "A1"
    },
    "preferredLanguage": {
      "type": "string",
      "title": "Preferredlanguage",
      "default": "English"
    },
    "createdAt": {
      "type": "string",
      "format": "date-time",
      "title": "Createdat"
    }
  },
  "type": "object",
  "required": [
    "id",
    "email",
    "displayName",
    "level",
    "xp",
    "createdAt"
  ],
  "title": "UserResponse"
}
```

## ValidationError

```json
{
  "properties": {
    "loc": {
      "items": {
        "anyOf": [
          {
            "type": "string"
          },
          {
            "type": "integer"
          }
        ]
      },
      "type": "array",
      "title": "Location"
    },
    "msg": {
      "type": "string",
      "title": "Message"
    },
    "type": {
      "type": "string",
      "title": "Error Type"
    },
    "input": {
      "title": "Input"
    },
    "ctx": {
      "type": "object",
      "title": "Context"
    }
  },
  "type": "object",
  "required": [
    "loc",
    "msg",
    "type"
  ],
  "title": "ValidationError"
}
```

## VocabularyCreate

```json
{
  "properties": {
    "word": {
      "type": "string",
      "maxLength": 120,
      "minLength": 1,
      "title": "Word"
    },
    "translation": {
      "type": "string",
      "maxLength": 300,
      "minLength": 1,
      "title": "Translation"
    },
    "example": {
      "type": "string",
      "maxLength": 1000,
      "title": "Example",
      "default": ""
    },
    "lessonId": {
      "anyOf": [
        {
          "type": "string",
          "format": "uuid"
        },
        {
          "type": "null"
        }
      ],
      "title": "Lessonid"
    }
  },
  "type": "object",
  "required": [
    "word",
    "translation"
  ],
  "title": "VocabularyCreate"
}
```

## VocabularyResponse

```json
{
  "properties": {
    "word": {
      "type": "string",
      "maxLength": 120,
      "minLength": 1,
      "title": "Word"
    },
    "translation": {
      "type": "string",
      "maxLength": 300,
      "minLength": 1,
      "title": "Translation"
    },
    "example": {
      "type": "string",
      "maxLength": 1000,
      "title": "Example",
      "default": ""
    },
    "lessonId": {
      "anyOf": [
        {
          "type": "string",
          "format": "uuid"
        },
        {
          "type": "null"
        }
      ],
      "title": "Lessonid"
    },
    "id": {
      "type": "string",
      "format": "uuid",
      "title": "Id"
    },
    "learned": {
      "type": "boolean",
      "title": "Learned"
    },
    "dueAt": {
      "type": "string",
      "format": "date-time",
      "title": "Dueat"
    },
    "createdAt": {
      "type": "string",
      "format": "date-time",
      "title": "Createdat"
    }
  },
  "type": "object",
  "required": [
    "word",
    "translation",
    "id",
    "learned",
    "dueAt",
    "createdAt"
  ],
  "title": "VocabularyResponse"
}
```

## VocabularyStatsResponse

```json
{
  "properties": {
    "wordsLearned": {
      "type": "integer",
      "title": "Wordslearned"
    }
  },
  "type": "object",
  "required": [
    "wordsLearned"
  ],
  "title": "VocabularyStatsResponse"
}
```

## VocabularyUpdate

```json
{
  "properties": {
    "learned": {
      "type": "boolean",
      "title": "Learned"
    }
  },
  "type": "object",
  "required": [
    "learned"
  ],
  "title": "VocabularyUpdate"
}
```

[Backend index](README.md)
