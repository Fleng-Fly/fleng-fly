# Secrets management

Keep JWT/provider/SMTP secrets, database credentials and reviewer/demo credentials in private host/environment stores or ignored local artifacts. Never place them under frontend/, reports, examples or Git. SecretStr masks ordinary representations but cannot make arbitrary debug logging safe.

Production validates JWT entropy-related minimums/development-value rejection, Secure cookies and exact HTTPS origins. AI/SMTP default off. Templates are references, not live environment changes. Do not print private .env or credential-bearing URLs for diagnosis.

DB diagnostics intentionally sanitize metadata and Origin logs are bounded, but unexpected-error logs need access controls/retention. No automated rotation service exists. Suspected exposure needs provider/host rotation, appropriate session revocation and private history review without publishing values.

[Section index](README.md) · [Documentation home](../README.md)
