# Fleng VPS deployment (Debian 13, nginx + systemd + native PostgreSQL)

Target: FastAPI + PostgreSQL on one VPS, nginx reverse proxy with Let's Encrypt on a
temporary `<IP-with-dashes>.sslip.io` hostname, Netlify frontend unchanged until the
owner switches the proxy. Full runbook and rationale: [docs/09-deployment/vps.md](../docs/09-deployment/vps.md).

| File | Installed to |
| --- | --- |
| `fleng.env.example` | `/etc/fleng/fleng.env` (root:fleng 0640, real secrets, never committed) |
| `systemd/fleng.service` | `/etc/systemd/system/fleng.service` |
| `nginx/fleng.conf` | `/etc/nginx/sites-available/fleng` (replace `__HOSTNAME__`) |
| `backup/fleng-backup.sh` | `/usr/local/sbin/fleng-backup` |
| `backup/fleng-restore-check.sh` | `/usr/local/sbin/fleng-restore-check` |
| `systemd/fleng-backup.service`, `.timer` | `/etc/systemd/system/` |

Nothing here is applied automatically. Data transfer from Render is **not** part of
this deployment and needs a separate decision.

## Enabling Fleng AI on an existing server

Fleng AI shows "Unavailable" until **all five** values are set; the two prices are mandatory so
spend can be bounded (an unknown price is never treated as free). No migration is needed (AI tables
ship with the normal `alembic upgrade head`). Do not overwrite `/etc/fleng/fleng.env`; append only
the missing keys.

```sh
# 1. Check which keys exist, without printing values
sudo grep -oE '^(AI_ENABLED|OPENROUTER_API_KEY|OPENROUTER_MODEL|AI_INPUT_PRICE_PER_MTOK_USD|AI_OUTPUT_PRICE_PER_MTOK_USD|AI_DAILY_BUDGET_USD)=' /etc/fleng/fleng.env

# 2. Edit (add/fill the missing keys; values come from the OpenRouter model page)
sudo cp -a /etc/fleng/fleng.env /etc/fleng/fleng.env.bak-$(date +%F)
sudoedit /etc/fleng/fleng.env
#   AI_ENABLED=true
#   OPENROUTER_API_KEY=<backend-only key>
#   OPENROUTER_MODEL=<provider/model>      # fixed model: no openrouter/* and no :online
#   AI_INPUT_PRICE_PER_MTOK_USD=<USD per 1M input tokens>
#   AI_OUTPUT_PRICE_PER_MTOK_USD=<USD per 1M output tokens>
#   AI_DAILY_BUDGET_USD=1.00

# 3. Deploy this code (adds `reason` to /ai/status), then restart
cd /opt/fleng && git pull --ff-only
sudo systemctl restart fleng.service
sudo systemctl status fleng.service --no-pager

# 4. Verify (the status call needs a signed-in session: DevTools > Network > /api/v1/ai/status)
#    Expected: {"available":true,"reason":null,"maxInputChars":500}
#    Otherwise `reason` is one of: disabled, missing_api_key, missing_model, missing_pricing.
sudo journalctl -u fleng.service -n 50 --no-pager
```

Then open Fleng AI in the browser, send one short message and confirm the streamed answer and that
it appears in the history. Limits (30 messages/day, 500 characters, 800 output tokens, $1/day, one
active request per learner) stay in force.
