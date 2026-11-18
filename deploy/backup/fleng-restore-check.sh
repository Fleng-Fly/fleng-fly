#!/usr/bin/env bash
# Restore drill: loads the newest daily dump into a NEW temporary database, counts rows,
# then drops only that temporary database. The live database is never touched.
# Run as the postgres user. Refuses to run if the temporary database already exists.
set -euo pipefail
umask 077
BACKUP_DIR="${FLENG_BACKUP_DIR:-/var/backups/fleng}"
CHECK_DB="fleng_restore_check"

dump="$(ls -1t "$BACKUP_DIR"/daily/fleng-*.dump | head -n1)"
( cd "$BACKUP_DIR/daily" && sha256sum --check "$(basename "$dump").sha256" )

if psql -tAc "SELECT 1 FROM pg_database WHERE datname='$CHECK_DB'" | grep -q 1; then
  echo "$CHECK_DB already exists; inspect and drop it manually" >&2
  exit 1
fi
createdb "$CHECK_DB"
trap 'dropdb --if-exists "$CHECK_DB"' EXIT
pg_restore --dbname="$CHECK_DB" --exit-on-error --single-transaction --no-owner --no-acl "$dump"
psql -d "$CHECK_DB" -tAc "SELECT 'alembic_version=' || version_num FROM alembic_version"
psql -d "$CHECK_DB" -tAc "SELECT 'users=' || count(*) FROM users"
echo "restore check ok: $(basename "$dump")"
