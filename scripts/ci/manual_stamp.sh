#!/usr/bin/env bash
set -euo pipefail

: "${SYNC_DATABASE_URL:?SYNC_DATABASE_URL must be set}"
echo "⚠️ THIS IS A MANUAL/PROTECTED OPERATION: alembic stamp head"
echo "Stamping head (mark migrations as applied without running SQL)"
alembic -c alembic.ini stamp head
echo "Done. alembic_version set to head."
