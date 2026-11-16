# Cors and origins

Credentialed CORS uses explicit origins from comma-separated CORS_ORIGIN plus validated RENDER_EXTERNAL_URL. Production entries require exact HTTPS origins without path/query/fragment/credentials. RENDER_EXTERNAL_URL is trusted server configuration, not a client forwarding header.

Register/login/refresh/logout separately reject supplied untrusted Origin (403), accepting own scheme/host and configured origins. Missing Origin is allowed. CORS is not authorization or a substitute for the cookie guard.

TLS termination can leave ASGI scheme HTTP while browser Origin is HTTPS; configure the public origin. run.py disables proxy headers unless TRUSTED_PROXY_IPS is configured and overrides wildcard platform defaults. Without forwarding trust, clients can share ingress IP quota; wildcard trust can permit spoofing. Verify real ingress and restrict upstream access.

[Section index](README.md) · [Documentation home](../README.md)
