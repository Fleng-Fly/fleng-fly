# Input validation

Pydantic validates emails/UUIDs/enums/lengths/query bounds. AI and flashcard request models forbid extras; CamelModel does not globally forbid unknown fields. Body middleware caps bytes at 128KiB by default. Validation envelopes omit raw input.

Bound SQLAlchemy expressions and database unique/FK/CHECK constraints supplement service rules. Browser theory/chat uses safe text nodes; that does not establish comprehensive CSP/security headers or XSS immunity.

Server keys and bounded answers control grading; invalid choices are rejected. Structured AI validation checks shape, not linguistic correctness. Public uploaded-file processing is not implemented.

[Section index](README.md) · [Documentation home](../README.md)
