# Fleng AI

The AI implementation lives in `backend/app/modules/ai/`, inside the FastAPI
monolith. This directory is a documentation entry point, not a separate service.

- `provider.py`: async OpenRouter HTTP transport and provider protocol.
- `prompts.py`: trusted tutor instructions and untrusted context separation.
- `context.py`: bounded learner analytics and deterministic recommendations.
- `service.py`: quotas, complete-turn persistence and structured validation.
- `router.py` / `schemas.py`: authenticated API, JSON and optional SSE.

Setup, limits, examples, testing and limitations: [docs/ai.md](../docs/ai.md).
No AI code or provider key is shipped to the frontend. The model cannot modify
user records, XP, achievements or official grades.
