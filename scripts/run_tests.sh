#!/usr/bin/env bash
set -euo pipefail

COMPOSE_ARGS="-f docker-compose.test.yml --env-file .env.test"

echo "🧹 Cleaning up previous containers..."
docker compose $COMPOSE_ARGS down -v --remove-orphans || true

echo "🚀 Starting isolated test environment..."
docker compose $COMPOSE_ARGS up -d test_db redis minio

echo "⏳ Waiting for database to be ready..."
for i in {1..20}; do
  if docker compose $COMPOSE_ARGS exec -T test_db pg_isready -U ${POSTGRES_USER:-saasuser} -d ${POSTGRES_DB:-saasdb_test} > /dev/null 2>&1; then
    echo "✅ Database is ready!"
    break
  fi
  echo "⏳ Waiting... ($i/20)"
  sleep 2
done

echo "🧪 Running pytest (inside test bot container)..."
docker compose $COMPOSE_ARGS run --rm bot pytest -vv \
  --maxfail=1 \
  --disable-warnings \
  --tb=short \
  --log-cli-level=INFO \
  --color=yes

exit_code=$?
echo "🧾 pytest finished with code: $exit_code"

echo "🧹 Cleaning up test environment..."
docker compose $COMPOSE_ARGS down -v --remove-orphans || true

if [ $exit_code -eq 0 ]; then
  echo "✅ Tests finished successfully!"
else
  echo "❌ Some tests failed!"
fi

exit $exit_code
