#!/bin/sh

# backups/restore_db.sh
# Восстановление базы данных из сжатого бэкапа .sql.gz

set -e

if [ -z "$1" ]; then
  echo "❌ Usage: /backups/restore_db.sh <backup_file.sql.gz>"
  exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
  echo "❌ Backup file not found: $BACKUP_FILE"
  exit 1
fi

HOST="${POSTGRES_HOST:-db}"
PORT="${POSTGRES_PORT:-5432}"
USER="${POSTGRES_USER:-saasuser}"
DB="${POSTGRES_DB:-saasdb}"
PASS="${POSTGRES_PASSWORD:-saaspass}"

echo "♻️  Starting restore from ${BACKUP_FILE}..."
export PGPASSWORD="${PASS}"

# Удаляем старую схему (-c), восстанавливаем из дампа
gunzip -c "$BACKUP_FILE" | pg_restore -h "$HOST" -p "$PORT" -U "$USER" -d "$DB" -c

echo "✅ Restore completed successfully for database: ${DB}"
