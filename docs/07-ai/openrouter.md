# Openrouter

Enable only on the backend with AI_ENABLED=true, OPENROUTER_API_KEY and OPENROUTER_MODEL=provider/model. No default paid model is selected. OPENROUTER_BASE_URL defaults https://openrouter.ai/api/v1 and requires HTTPS without embedded credentials/query/fragment. Keep keys out of frontend files and browser variables.

The provider uses httpx completions/streams and sanitizes upstream failures. AI_STRUCTURED_OUTPUTS controls optional schema-oriented requests; application Pydantic validation still checks output. [Configuration reference](../12-reference/configuration-reference.md) gives timeout/token/character limits.

/ai/status reports configuration readiness/maxInputChars without a paid probe. It is not upstream availability/correctness assurance. Mocked tests do not establish live pricing, billing or model behavior; ordinary development needs no provider call.

[Section index](README.md) · [Documentation home](../README.md)
