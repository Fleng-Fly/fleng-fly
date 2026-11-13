# Prompts

Server-owned builders combine educational instructions with bounded user/context data. context.py resolves published lesson/exercise and caller progress; arbitrary IDs cannot bypass visibility. Grading secrets are excluded before submission; owned attempt feedback can inform explanations.

History/input/output bounds limit context. Users cannot supply arbitrary system/tool roles and generated code is not executed. Structured explanation/exercise outputs must satisfy Pydantic schemas.

Treat all user/provider text as untrusted. Delimiters do not solve prompt injection. No private conversations or full prompt content are copied here. Review prompt changes for answer disclosure, excessive personal context and unsupported teaching claims.

[Section index](README.md) · [Documentation home](../README.md)
