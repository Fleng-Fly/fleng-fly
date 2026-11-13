# Rate limiting

Persistent RequestLimit windows use hashed scope keys. Login defaults 20/IP/minute and 10/email/minute; register 10/IP/hour. IP attempts commit before expensive auth, including rejected credentials. Exceeding returns 429 RATE_LIMITED with window-aligned Retry-After.

Reset defaults 5/hour per IP and email where applicable. AI uses minute/day/token reservations/capacity. Password workers are separately bounded.

There is no universal DDoS/edge defense or refresh-specific quota. The ASGI peer determines IP unless forwarding comes through explicitly trusted ingress. Shared proxy IPs can cause contention; multi-instance load resistance is not established by SQLite tests. [AI limits](../07-ai/limits-and-errors.md) describes reservations.

[Section index](README.md) · [Documentation home](../README.md)
