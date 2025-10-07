#!/usr/bin/env bash
set -euo pipefail

: "${SYNC_DATABASE_URL:?SYNC_DATABASE_URL must be set}"

# Проверка состояния
bash scripts/ci/check_alembic_state.sh
rc=$?

if [[ $rc -eq 0 ]]; then
  echo "✅ DB clean or alembic_version present — выполняем alembic upgrade head"
  alembic -c alembic.ini upgrade head
  exit $?
elif [[ $rc -eq 2 ]]; then
  echo "❌ Отказ: в БД есть таблицы, но нет alembic_version. Не буду запускать upgrade."
  echo "Действия:"
  echo "  - локально: если это dev и можно пересоздать БД — сделай make reset"
  echo "  - если DB должна оставаться и схема совпадает с миграциями — выполните вручную защищённый job 'migrations_manual_stamp' (alembic stamp head)"
  exit 3
else
  echo "Unknown status from check_alembic_state.sh: $rc"
  exit 4
fi
