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
