#!/usr/bin/env bash
# Local PostgreSQL backup for Fleng. Runs as the postgres user (peer auth), never touches
# the live database beyond a read-only pg_dump. Install to /usr/local/sbin/fleng-backup.
# Retention: 7 daily, 4 weekly (Sunday), 3 monthly (1st). Optional off-host hook below.
set -euo pipefail
umask 077

BACKUP_DIR="${FLENG_BACKUP_DIR:-/var/backups/fleng}"
DB_NAME="${FLENG_BACKUP_DB:-fleng}"
# Off-host is disabled by default. Set FLENG_OFFHOST_HOOK in /etc/fleng/backup.conf to an
# executable that receives the new dump path (e.g. an rsync/rclone wrapper); it should
# upload ALREADY ENCRYPTED data. A hook failure fails the job but keeps the local copy.
OFFHOST_HOOK="${FLENG_OFFHOST_HOOK:-}"

mkdir -p "$BACKUP_DIR/daily" "$BACKUP_DIR/weekly" "$BACKUP_DIR/monthly"
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
tmp="$(mktemp "$BACKUP_DIR/.dump.XXXXXX")"
trap 'rm -f "$tmp"' EXIT

pg_dump --format=custom --no-owner --no-acl --dbname="$DB_NAME" --file="$tmp"
pg_restore --list "$tmp" >/dev/null   # archive must be readable before it is kept

out="$BACKUP_DIR/daily/fleng-$stamp.dump"
mv "$tmp" "$out"
trap - EXIT
( cd "$BACKUP_DIR/daily" && sha256sum "fleng-$stamp.dump" > "fleng-$stamp.dump.sha256" )

if [ "$(date -u +%u)" = "7" ]; then
  cp -p "$out" "$out.sha256" "$BACKUP_DIR/weekly/"
fi
if [ "$(date -u +%d)" = "01" ]; then
  cp -p "$out" "$out.sha256" "$BACKUP_DIR/monthly/"
fi

find "$BACKUP_DIR/daily" -type f -name 'fleng-*' -mtime +7 -delete
find "$BACKUP_DIR/weekly" -type f -name 'fleng-*' -mtime +28 -delete
find "$BACKUP_DIR/monthly" -type f -name 'fleng-*' -mtime +93 -delete

echo "backup ok: $(basename "$out") $(stat -c %s "$out") bytes"

if [ -n "$OFFHOST_HOOK" ]; then
  "$OFFHOST_HOOK" "$out"
fi
