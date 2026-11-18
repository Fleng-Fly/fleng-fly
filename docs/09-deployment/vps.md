# VPS deployment (Debian 13)

Status: **prepared, not executed.** The files in [`deploy/`](../../deploy/README.md)
were written and statically reviewed locally; no VPS, nginx, systemd or PostgreSQL
was available to run them. No Render/Netlify setting, production database or secret
was touched.

## Topology

```
browser → Netlify (static, unchanged) ──/api/* proxy (later, owner decision)──┐
browser → https://<IP-dashed>.sslip.io ───────────────────────────────────────┤
                                       nginx :443/:80 → 127.0.0.1:3001 (uvicorn, 1 worker, systemd)
                                                         → PostgreSQL 127.0.0.1:5432
                                                         → OpenRouter (HTTPS, AI disabled by default)
```

The backend also serves `frontend/`, so the sslip.io origin is a working copy of the site.

## `HOST` setting

`run.py` now listens on `HOST` (Settings field `host`). Unset it is `127.0.0.1`,
so uvicorn is never reachable except through nginx. **Render exception:** when
`RENDER_EXTERNAL_URL` is present (Render supplies it) and `HOST` is unset, the
launcher keeps `0.0.0.0`, which Render's routing requires; no Render variable change
is needed. Set `HOST=0.0.0.0` explicitly only for a container/host that needs it.
Direct `uvicorn` use and the root `Procfile` are unchanged.

## Release order

1. Harden the host: non-root admin, SSH keys only, `ufw` allow 22/80/443, fail2ban,
   unattended-upgrades.
2. `apt install python3 python3-venv git nginx postgresql certbot python3-certbot-nginx`.
3. Create role/database `fleng` with a server-generated password.
4. Clone as the service user, create venv, `pip install -c backend/constraints.txt ./backend`.
5. Write `/etc/fleng/fleng.env` from [`fleng.env.example`](../../deploy/fleng.env.example).
6. `alembic upgrade head` (explicit), compare `alembic current` with `heads`.
7. Install and start `fleng.service`; check `/api/v1/health/ready` on loopback.
8. Install nginx site, obtain the certificate, verify HTTPS and that `:3001` is closed.
9. Enable the backup timer, run one backup and one restore drill.
10. Application checks: register, login, reload (refresh cookie), submit a lesson twice
    (XP once), reject a foreign `Origin`, SSE only if AI is enabled.

## Behaviour to know

- `run.py` migrates only an **empty** PostgreSQL schema; an existing older schema needs
  the explicit `alembic upgrade head`. It also publishes the packaged A0–B2 catalog
  on start. A later Render-data transfer (`app.db.transfer`) requires a migrated,
  otherwise **empty** target, so it must happen **before** the first service start on
  that database, or on a separate staging database. Plan this with the owner first.
- `TRUSTED_PROXY_IPS=127.0.0.1` makes uvicorn trust nginx's `X-Forwarded-For`, which
  nginx overwrites with `$remote_addr`. Behind the Netlify `/api/*` proxy `$remote_addr`
  is a Netlify address, so login/registration rate limits would be shared by every
  user. This is verified and fixed **separately after the proxy is configured**
  (see plans/roadmap.md).
- Let's Encrypt on `*.sslip.io` is subject to shared rate limits of that domain and
  depends on a third-party DNS service; it is temporary until the real domain exists.
- `CORS_ORIGIN` must list exact HTTPS origins: Netlify plus the sslip.io host.

## Backups

`fleng-backup.timer` runs daily at 03:15 UTC as `postgres`: `pg_dump` custom format,
archive verified with `pg_restore --list`, SHA-256 file, retention 7 daily / 4 weekly /
3 monthly under `/var/backups/fleng` (0700). Local files on the same disk are **not**
disaster protection. Off-host copy is prepared but disabled: set `FLENG_OFFHOST_HOOK`
in `/etc/fleng/backup.conf` to an executable receiving the dump path (it should upload
encrypted data). `fleng-restore-check` restores the newest dump into a temporary new
database, prints `alembic_version` and user count, then drops only that temporary
database. Never restore over the live database.

[Section index](README.md) · [Documentation home](../README.md)
