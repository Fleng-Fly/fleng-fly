# Ai api

Bearer identity on every route. History/delete enforce ownership (404). Provider routes require configured/enabled OpenRouter; status is config readiness, recommendations deterministic. Service input can be stricter than schema. AI_INPUT_LIMIT=422; AI_HISTORY_LIMIT/AI_CONVERSATION_LIMIT/AI_REQUEST_DUPLICATE=409; AI_BUSY/AI_BUDGET_LIMIT=429; AI_UNAVAILABLE=503; AI_TIMEOUT=504 before headers. Midstream error events preserve HTTP 200. Models: AIConversation, AIMessage, AIUsage.

Shared runtime failures: 413 body overflow, 422 declared schema validation, 503 DATABASE_UNAVAILABLE and 500 unexpected error. Protected calls add 401 missing/invalid identity. See [error handling](error-handling.md) and [complete schemas](api-schemas.md). Module-specific rules above apply to each operation.

## `GET /api/v1/ai/status`

Status

Authentication/permissions: Bearer JWT, owner scoped where applicable.

Parameters: none.

Request body: none.

Declared responses:

- **200**: Successful Response; no declared JSON model.

Errors/permissions: module-specific and shared runtime rules above apply. No caller-selected owner override exists.

Example request: substitute discovered slugs/UUIDs; refresh/logout cookie jars require prior login. Example passwords/tokens are synthetic.

```sh
curl -i -X GET http://localhost:3001/api/v1/ai/status \
  -H "Authorization: Bearer $FLENG_ACCESS_TOKEN"
```

Unmodeled JSON response: see the explicit status/recommendations contracts below.

## `POST /api/v1/ai/chat`

Chat

Authentication/permissions: Bearer JWT, owner scoped where applicable.

Parameters: none.

Request body: JSON `ChatRequest` (required=True), defined in [schemas](api-schemas.md).

Declared responses:

- **200**: Successful Response; `{"$ref": "#/components/schemas/ChatResponse"}`.
- **422**: Validation Error; `{"$ref": "#/components/schemas/HTTPValidationError"}`.

Errors/permissions: module-specific and shared runtime rules above apply. No caller-selected owner override exists.

Example request: substitute discovered slugs/UUIDs; refresh/logout cookie jars require prior login. Example passwords/tokens are synthetic.

```sh
curl -i -X POST http://localhost:3001/api/v1/ai/chat \
  -H "Authorization: Bearer $FLENG_ACCESS_TOKEN" \
  -H 'Content-Type: application/json' \
  --data '{"message": "Explain the present simple.", "correctGrammar": true}'
```

Synthetic response shape (not a seeded/live result):

```json
{
  "conversationId": "00000000-0000-4000-8000-000000000001",
  "message": {
    "id": "00000000-0000-4000-8000-000000000001",
    "role": "example",
    "content": "example",
    "model": "example",
    "usage": {},
    "createdAt": "2026-11-13T00:00:00Z"
  }
}
```

## `GET /api/v1/ai/conversations`

Conversations

Authentication/permissions: Bearer JWT, owner scoped where applicable.

| Parameter | In | Required | Exact schema |
| --- | --- | --- | --- |
| limit | query | False | `{"type": "integer", "maximum": 100, "minimum": 1, "default": 20, "title": "Limit"}` |
| offset | query | False | `{"type": "integer", "minimum": 0, "default": 0, "title": "Offset"}` |

Request body: none.

Declared responses:

- **200**: Successful Response; `{"type": "array", "items": {"$ref": "#/components/schemas/ConversationResponse"}, "title": "Response Conversations Api V1 Ai Conversations Get"}`.
- **422**: Validation Error; `{"$ref": "#/components/schemas/HTTPValidationError"}`.

Errors/permissions: module-specific and shared runtime rules above apply. No caller-selected owner override exists.

Example request: substitute discovered slugs/UUIDs; refresh/logout cookie jars require prior login. Example passwords/tokens are synthetic.

```sh
curl -i -X GET http://localhost:3001/api/v1/ai/conversations \
  -H "Authorization: Bearer $FLENG_ACCESS_TOKEN"
```

Synthetic response shape (not a seeded/live result):

```json
[]
```

## `GET /api/v1/ai/conversations/{conversation_id}`

History

Authentication/permissions: Bearer JWT, owner scoped where applicable.

| Parameter | In | Required | Exact schema |
| --- | --- | --- | --- |
| conversation_id | path | True | `{"type": "string", "format": "uuid", "title": "Conversation Id"}` |
| limit | query | False | `{"type": "integer", "maximum": 100, "minimum": 1, "default": 50, "title": "Limit"}` |
| offset | query | False | `{"type": "integer", "minimum": 0, "default": 0, "title": "Offset"}` |

Request body: none.

Declared responses:

- **200**: Successful Response; `{"type": "array", "items": {"$ref": "#/components/schemas/MessageResponse"}, "title": "Response History Api V1 Ai Conversations  Conversation Id  Get"}`.
- **422**: Validation Error; `{"$ref": "#/components/schemas/HTTPValidationError"}`.

Errors/permissions: module-specific and shared runtime rules above apply. No caller-selected owner override exists.

Example request: substitute discovered slugs/UUIDs; refresh/logout cookie jars require prior login. Example passwords/tokens are synthetic.

```sh
curl -i -X GET http://localhost:3001/api/v1/ai/conversations/00000000-0000-4000-8000-000000000001 \
  -H "Authorization: Bearer $FLENG_ACCESS_TOKEN"
```

Synthetic response shape (not a seeded/live result):

```json
[]
```

## `DELETE /api/v1/ai/conversations/{conversation_id}`

Remove

Authentication/permissions: Bearer JWT, owner scoped where applicable.

| Parameter | In | Required | Exact schema |
| --- | --- | --- | --- |
| conversation_id | path | True | `{"type": "string", "format": "uuid", "title": "Conversation Id"}` |

Request body: none.

Declared responses:

- **204**: Successful Response; no declared JSON model.
- **422**: Validation Error; `{"$ref": "#/components/schemas/HTTPValidationError"}`.

Errors/permissions: module-specific and shared runtime rules above apply. No caller-selected owner override exists.

Example request: substitute discovered slugs/UUIDs; refresh/logout cookie jars require prior login. Example passwords/tokens are synthetic.

```sh
curl -i -X DELETE http://localhost:3001/api/v1/ai/conversations/00000000-0000-4000-8000-000000000001 \
  -H "Authorization: Bearer $FLENG_ACCESS_TOKEN"
```

Unmodeled JSON response: see the explicit status/recommendations contracts below.

## `POST /api/v1/ai/explain`

Explain

Authentication/permissions: Bearer JWT, owner scoped where applicable.

Parameters: none.

Request body: JSON `ExplainRequest` (required=True), defined in [schemas](api-schemas.md).

Declared responses:

- **200**: Successful Response; `{"$ref": "#/components/schemas/Explanation"}`.
- **422**: Validation Error; `{"$ref": "#/components/schemas/HTTPValidationError"}`.

Errors/permissions: module-specific and shared runtime rules above apply. No caller-selected owner override exists.

Example request: substitute discovered slugs/UUIDs; refresh/logout cookie jars require prior login. Example passwords/tokens are synthetic.

```sh
curl -i -X POST http://localhost:3001/api/v1/ai/explain \
  -H "Authorization: Bearer $FLENG_ACCESS_TOKEN" \
  -H 'Content-Type: application/json' \
  --data '{"studentAnswer": "She go to school.", "topic": "Present simple"}'
```

Synthetic response shape (not a seeded/live result):

```json
{
  "explanation": "example",
  "correctExample": "example",
  "rule": "example",
  "hint": ""
}
```

## `POST /api/v1/ai/generate-exercise`

Generate

Authentication/permissions: Bearer JWT, owner scoped where applicable.

Parameters: none.

Request body: JSON `GenerateRequest` (required=True), defined in [schemas](api-schemas.md).

Declared responses:

- **200**: Successful Response; `{"$ref": "#/components/schemas/GeneratedExercise"}`.
- **422**: Validation Error; `{"$ref": "#/components/schemas/HTTPValidationError"}`.

Errors/permissions: module-specific and shared runtime rules above apply. No caller-selected owner override exists.

Example request: substitute discovered slugs/UUIDs; refresh/logout cookie jars require prior login. Example passwords/tokens are synthetic.

```sh
curl -i -X POST http://localhost:3001/api/v1/ai/generate-exercise \
  -H "Authorization: Bearer $FLENG_ACCESS_TOKEN" \
  -H 'Content-Type: application/json' \
  --data '{"level": "A1", "topic": "Present simple", "difficulty": "easy", "exerciseType": "multiple_choice"}'
```

Synthetic response shape (not a seeded/live result):

```json
{
  "type": "multiple_choice",
  "prompt": "example",
  "options": [
    "She goes to school.",
    "She go to school."
  ],
  "answer": "She goes to school.",
  "explanation": "example",
  "practiceOnly": true
}
```

## `GET /api/v1/ai/recommendations`

Recommendations

Authentication/permissions: Bearer JWT, owner scoped where applicable.

Parameters: none.

Request body: none.

Declared responses:

- **200**: Successful Response; no declared JSON model.

Errors/permissions: module-specific and shared runtime rules above apply. No caller-selected owner override exists.

Example request: substitute discovered slugs/UUIDs; refresh/logout cookie jars require prior login. Example passwords/tokens are synthetic.

```sh
curl -i -X GET http://localhost:3001/api/v1/ai/recommendations \
  -H "Authorization: Bearer $FLENG_ACCESS_TOKEN"
```

Unmodeled JSON response: see the explicit status/recommendations contracts below.

## `POST /api/v1/ai/chat/stream`

Stream Chat

Authentication/permissions: Bearer JWT, owner scoped where applicable.

Parameters: none.

Request body: JSON `ChatRequest` (required=True), defined in [schemas](api-schemas.md).

Declared responses:

- **200**: Successful Response; no declared JSON model.
- **422**: Validation Error; `{"$ref": "#/components/schemas/HTTPValidationError"}`.

Errors/permissions: module-specific and shared runtime rules above apply. No caller-selected owner override exists.

Example request: substitute discovered slugs/UUIDs; refresh/logout cookie jars require prior login. Example passwords/tokens are synthetic.

```sh
curl -i -X POST http://localhost:3001/api/v1/ai/chat/stream \
  -H "Authorization: Bearer $FLENG_ACCESS_TOKEN" \
  -H 'Content-Type: application/json' \
  --data '{"message": "Explain the present simple.", "correctGrammar": true}'
```

Example frames:

```text
event: delta
data: {"content":"Hello"}

event: error
data: {"code":"AI_TIMEOUT","message":"AI stream did not complete. Reload history before sending again."}

```

Successful completion uses done with ChatResponse; these frames illustrate a failed partial stream.

[Backend index](README.md) · [Schema reference](api-schemas.md)

## Unmodeled response contracts

GET status returns an object with available (boolean) and maxInputChars (integer), for example:

```json
{"available":false,"maxInputChars":4000}
```

GET recommendations returns level, reviewTopics (slug/topic/missed objects), reviewWords (strings), nextLessons (slug/title objects), and reason. Synthetic empty-state example:

```json
{"level":"A1","reviewTopics":[],"reviewWords":[],"nextLessons":[],"reason":"Review incorrect submissions and unlearned words, then continue your level."}
```

These handlers have no declared response_model; source/context tests establish these shapes rather than a generated Pydantic schema.
