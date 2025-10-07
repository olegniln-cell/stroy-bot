#!/usr/bin/env bash
# scripts/ci/wait_for_minio.sh
# Ждёт, пока MinIO станет ready (HTTP 200 /minio/health/live).
# Usage: bash scripts/ci/wait_for_minio.sh <host> <port> [timeout_seconds]
# Example: bash scripts/ci/wait_for_minio.sh minio 9000 120

set -euo pipefail

HOST="${1:-minio}"
PORT="${2:-9000}"
TIMEOUT="${3:-120}"  # seconds
SLEEP=3

echo "Waiting for MinIO at ${HOST}:${PORT} (timeout ${TIMEOUT}s)..."

end=$((SECONDS + TIMEOUT))
while true; do
  if curl -sSf "http://${HOST}:${PORT}/minio/health/live" >/dev/null 2>&1; then
    echo "✅ MinIO is healthy at ${HOST}:${PORT}"
    exit 0
  fi

  if [ "$SECONDS" -ge "$end" ]; then
    echo "❌ Timeout waiting for MinIO at ${HOST}:${PORT}"
    exit 1
  fi

  echo "… MinIO not ready yet, sleeping ${SLEEP}s"
  sleep "${SLEEP}"
done
