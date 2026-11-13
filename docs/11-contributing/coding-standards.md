# Coding standards

Backend: Python 3.11+, FastAPI, SQLAlchemy async, Pydantic, Ruff/mypy. Frontend: plain HTML/CSS/browser JS modules. Project contract prohibits TypeScript, frontend frameworks/build steps and Node backend frameworks.

Use CamelModel boundaries and owner-scoped queries; preserve server grading/once-only XP. Schema changes need reviewed migrations with SQLite preservation and explicit PostgreSQL evidence.

Use safe text DOM rendering, shared api.js fetch and memory-only tokens. Keep provider credentials server-side and debug configuration/passwords/cookies out of logs. Test meaningful behavior rather than mirroring trivial implementation.

[Section index](README.md) · [Documentation home](../README.md)
