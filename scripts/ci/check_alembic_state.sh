#!/usr/bin/env bash
set -euo pipefail

: "${SYNC_DATABASE_URL:?SYNC_DATABASE_URL must be set (example: postgresql+psycopg2://user:pass@host:5432/db)}"
# psql принимает URI (если в CI установлен psql)
export PGSSLMODE=${PGSSLMODE:-disable}

# Проверим наличие таблицы alembic_version
AL_EXISTS=$(psql "$SYNC_DATABASE_URL" -Atc \
  "SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='alembic_version';" || echo "")

if [[ "$AL_EXISTS" == "1" ]]; then
  echo "alembic_version: present"
  exit 0
fi

# Считаем количество пользовательских таблиц
USER_TABLES=$(psql "$SYNC_DATABASE_URL" -Atc \
  "SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE' AND table_name <> 'alembic_version';")
USER_TABLES=${USER_TABLES:-0}
echo "alembic_version: absent; non-alembic user tables = $USER_TABLES"

if [[ "$USER_TABLES" -gt 0 ]]; then
  echo "⚠️ Database contains tables but no alembic_version. THIS IS DANGEROUS to auto-migrate."
  echo "If the schema in DB already matches migrations and you are absolutely sure -> run the protected manual job to 'alembic stamp head' once."
  exit 2
else
  echo "DB is empty (no user tables). Safe to run 'alembic upgrade head'."
  exit 0
fi
