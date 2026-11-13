# Environment variables

[Complete Settings reference](../12-reference/configuration-reference.md) lists every field/default/bound. Release-critical settings: APP_ENV=production, private random JWT_ACCESS_SECRET (>=32 characters), explicit DATABASE_URL, host PORT, Secure cookies, SameSite policy and exact HTTPS CORS_ORIGIN values separated by commas. RENDER_EXTERNAL_URL must be exact HTTPS; TRUSTED_PROXY_IPS defaults empty.

FRONTEND_DIR can override the static path. AI_ENABLED stays false until key/model and real transport are verified. RESET_DELIVERY stays disabled until SMTP and usable RESET_URL are configured; no reset-password page exists here. Provider/SMTP/database credentials belong only on the backend.

.env.production.example is not automatically loaded. Environment overrides optional .env files. Editing a template does not update hosting settings.

[Section index](README.md) · [Documentation home](../README.md)
