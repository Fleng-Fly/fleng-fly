# Configuration reference

Source: [Settings](../../backend/app/core/config.py). Uppercase field names are environment keys. Process environment overrides root .env, which overrides backend/.env. Defaults below are source declarations, not private values. Field expressions preserve exact bounds. Secrets are suppressed.

| Variable | Declared default/validation |
| --- | --- |
| `APP_ENV` | `'development'` |
| `PORT` | `Field(default=3001, ge=1, le=65535)` |
| `TRUSTED_PROXY_IPS` | `''` |
| `HTTP_MAX_BODY_BYTES` | `Field(default=131072, ge=1024, le=1048576)` |
| `DATABASE_URL` | `DEFAULT_DATABASE_URL` |
| `CORS_ORIGIN` | `'http://localhost:3000'` |
| `RENDER_EXTERNAL_URL` | `''` |
| `FRONTEND_DIR` | `None` |
| `AUTH_LOGIN_IP_PER_MINUTE` | `Field(default=20, ge=1)` |
| `AUTH_LOGIN_EMAIL_PER_MINUTE` | `Field(default=10, ge=1)` |
| `AUTH_REGISTER_IP_PER_HOUR` | `Field(default=10, ge=1)` |
| `JWT_ACCESS_SECRET` | `Private secret; empty except development-only JWT fallback; production JWT requires random >=32 characters` |
| `JWT_ALGORITHM` | `'HS256'` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `30` |
| `REFRESH_COOKIE_NAME` | `'fleng_refresh'` |
| `REFRESH_COOKIE_PATH` | `'/api/v1/auth'` |
| `COOKIE_SECURE` | `None` |
| `COOKIE_SAMESITE` | `'lax'` |
| `LEARNING_TIMEZONE` | `'UTC'` |
| `RESET_TOKEN_MINUTES` | `Field(default=30, ge=1, le=1440)` |
| `RESET_RATE_PER_HOUR` | `Field(default=5, ge=1)` |
| `RESET_DELIVERY` | `'disabled'` |
| `RESET_URL` | `'http://localhost:3001/reset-password.html'` |
| `SMTP_HOST` | `'localhost'` |
| `SMTP_PORT` | `Field(default=587, ge=1, le=65535)` |
| `SMTP_USERNAME` | `''` |
| `SMTP_PASSWORD` | `Private secret; empty except development-only JWT fallback; production JWT requires random >=32 characters` |
| `SMTP_FROM` | `'noreply@example.com'` |
| `SMTP_STARTTLS` | `True` |
| `AI_ENABLED` | `False` |
| `OPENROUTER_API_KEY` | `Private secret; empty except development-only JWT fallback; production JWT requires random >=32 characters` |
| `OPENROUTER_BASE_URL` | `'https://openrouter.ai/api/v1'` |
| `OPENROUTER_MODEL` | `''` |
| `AI_STRUCTURED_OUTPUTS` | `False` |
| `AI_MAX_OUTPUT_TOKENS` | `Field(default=800, ge=1, le=8192)` |
| `AI_MAX_INPUT_TOKENS` | `Field(default=24000, ge=1, le=128000)` |
| `AI_REQUEST_TIMEOUT` | `Field(default=30, gt=0, le=300)` |
| `AI_MAX_INPUT_CHARS` | `Field(default=4000, ge=1, le=16000)` |
| `AI_MAX_RESPONSE_CHARS` | `Field(default=16000, ge=1, le=64000)` |
| `AI_HISTORY_MESSAGES` | `Field(default=20, ge=2, le=100)` |
| `AI_HISTORY_CHARS` | `Field(default=16000, ge=1, le=100000)` |
| `AI_MESSAGES_PER_CONVERSATION` | `Field(default=200, ge=2, le=1000)` |
| `AI_CONVERSATIONS_PER_USER` | `Field(default=50, ge=1, le=500)` |
| `AI_REQUESTS_PER_MINUTE` | `Field(default=10, ge=1)` |
| `AI_DAILY_REQUESTS` | `Field(default=100, ge=1)` |
| `AI_DAILY_TOKEN_BUDGET` | `Field(default=100000, ge=1)` |
| `AI_CONCURRENCY` | `Field(default=4, ge=1, le=100)` |

DEFAULT_DATABASE_URL is sqlite+aiosqlite:///./data/fleng.db, resolved against backend/. COOKIE_SECURE=None derives from APP_ENV; production requires true. Production CORS/RENDER_EXTERNAL_URL require exact HTTPS origins. LEARNING_TIMEZONE resolves via ZoneInfo. OpenRouter model requires provider/model syntax and URL must be HTTPS without embedded credentials/query/fragment.

## Script/test environment

TEST_DATABASE_URL opts into PostgreSQL fixtures and is not a Settings field. Compose fixes POSTGRES_USER/PASSWORD/DB to local example values and reads only POSTGRES_PORT from the host, as in [docker-compose.yml](../../docker-compose.yml). PORT is also read directly by dev.mjs. run.py overrides platform FORWARDED_ALLOW_IPS with TRUSTED_PROXY_IPS. Preview supplies isolated Settings, never export its generated credentials. Validator budgets use explicit CLI flags.

See [configuration](../01-getting-started/configuration.md) and [deployment](../09-deployment/environment-variables.md).
