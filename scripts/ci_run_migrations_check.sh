#!/usr/bin/env bash
set -euo pipefail

# Параметры (если хочешь — не трогай)
PG_USER=saasuser
PG_PASS=saaspass
PG_DB=saasdb
PG_PORT=5432
CONTAINER=ci-postgres

# 1) Убиваем старый контейнер (если есть) и запускаем Postgres
docker rm -f $CONTAINER 2>/dev/null || true
docker run --name $CONTAINER -e POSTGRES_USER="$PG_USER" -e POSTGRES_PASSWORD="$PG_PASS" -e POSTGRES_DB="$PG_DB" -p ${PG_PORT}:5432 -d postgres:15

# 2) Ждём готовности БД
until docker exec $CONTAINER pg_isready -U "$PG_USER" -d "$PG_DB" >/dev/null 2>&1; do
  echo "waiting for postgres..."
  sleep 1
done
echo "postgres is ready"

# 3) Устанавливаем зависимости (в текущем окружении)
pip install -r requirements.txt

# 4) Подстраиваем DATABASE_URL (sync/async autodetect)
DBURL="postgresql://$PG_USER:$PG_PASS@localhost:${PG_PORT}/$PG_DB"
if grep -q "asyncpg" migrations/env.py 2>/dev/null || grep -q "create_async_engine" migrations/env.py 2>/dev/null; then
  DBURL="postgresql+asyncpg://$PG_USER:$PG_PASS@localhost:${PG_PORT}/$PG_DB"
fi
export DATABASE_URL="$DBURL"
echo "Using DATABASE_URL=$DATABASE_URL"

# 5) (опционально) проверка alembic (если доступна)
alembic check || true

# 6) Накатываем миграции на чистую БД — если упадёт, скрипт остановится
echo "Running: alembic upgrade head"
alembic upgrade head

# 7) Проверяем модели против БД
PYTHONPATH=. python scripts/check_models_vs_db.py

# 8) Запускаем smoke-интеграционные тесты
pytest tests/integration/smoke_tests.py --maxfail=1 --disable-warnings -q

# 9) Проверяем, что autogenerate не создал файлов
BEFORE=$(ls -1 migrations/versions 2>/dev/null | wc -l || echo 0)
alembic revision --autogenerate -m "ci-autogen-check" || true
AFTER=$(ls -1 migrations/versions 2>/dev/null | wc -l || echo 0)
if [ "$AFTER" -ne "$BEFORE" ]; then
  echo "❌ alembic autogenerate created new migration(s) — schema mismatch!"
  ls -la migrations/versions | tail -n 20
  rm -f migrations/versions/*ci-autogen-check*.py || true
  docker rm -f $CONTAINER || true
  exit 1
fi

echo "✅ SUCCESS: migrations applied and smoke tests passed"

# 10) Очистка
docker rm -f $CONTAINER || true
