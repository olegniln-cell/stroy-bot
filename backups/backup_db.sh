#!/bin/sh

# backups/backup_db.sh
# Простой pg_dump бэкап в папку ./backups

set -e

HOST="${POSTGRES_HOST:-db}"
PORT="${POSTGRES_PORT:-5432}"
USER="${POSTGRES_USER:-saasuser}"
DB="${POSTGRES_DB:-saasdb}"
PASS="${POSTGRES_PASSWORD:-saaspass}"
OUT_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d%H%M%S)
FNAME="${OUT_DIR}/backup_${DB}_${TIMESTAMP}.sql.gz"

mkdir -p "${OUT_DIR}"

export PGPASSWORD="${PASS}"
pg_dump -h "${HOST}" -p "${PORT}" -U "${USER}" -Fc "${DB}" | gzip > "${FNAME}"

echo "Backup saved to ${FNAME}"
