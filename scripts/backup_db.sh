#!/usr/bin/env bash
set -euo pipefail

DATE=$(date +%Y%m%d_%H%M%S)
DUMP_FILE="/backups/saasdb_$DATE.sql"

echo "📦 Dumping database..."
pg_dump --clean --if-exists -h db -U saasuser saasdb > "$DUMP_FILE"
echo "✅ Backup saved to $DUMP_FILE"
