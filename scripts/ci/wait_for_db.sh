#!/usr/bin/env bash
set -e

HOST="${1:-postgres}"
PORT="${2:-5432}"
USER="${3:-saasuser}"
MAX_RETRIES="${4:-120}"   # 60 секунд по умолчанию

echo "⏳ Waiting for Postgres at $HOST:$PORT (user=$USER)..."
for i in $(seq 1 $MAX_RETRIES); do
  if pg_isready -h "$HOST" -p "$PORT" -U "$USER" >/dev/null 2>&1; then
    echo "✅ Postgres is ready!"
    exit 0
  fi
  sleep 1
done

echo "❌ Postgres not ready after ${MAX_RETRIES}s"
exit 1
