#!/usr/bin/env bash

# saas_diagnose.sh
# Собирает snapshot состояния docker-compose infra + health + backups + hawk check
# Сохраняет в infra_report.txt

set -euo pipefail

OUTFILE="infra_report.txt"
TIMESTAMP=$(date --iso-8601=seconds 2>/dev/null || date +"%Y-%m-%dT%H:%M:%S%z")

echo "🧭 SaaS Infra Diagnostic — snapshot at $TIMESTAMP" > "$OUTFILE"
echo "==================================================" >> "$OUTFILE"
echo "" >> "$OUTFILE"

echo "### Basic system info" >> "$OUTFILE"
echo "Timestamp: $TIMESTAMP" >> "$OUTFILE"
uname -a >> "$OUTFILE" 2>&1 || true
echo "" >> "$OUTFILE"

# --- Docker Compose status ---

echo "--- docker-compose ps ---" >> "$OUTFILE"
if command -v docker-compose >/dev/null 2>&1; then
  docker-compose ps >> "$OUTFILE" 2>&1 || docker compose ps >> "$OUTFILE" 2>&1 || true
else
  echo "docker-compose not found" >> "$OUTFILE"
fi
echo "" >> "$OUTFILE"

# --- docker system df ---

echo "--- docker system df ---" >> "$OUTFILE"
docker system df >> "$OUTFILE" 2>&1 || true
echo "" >> "$OUTFILE"

# --- docker ps -a ---

echo "--- docker ps -a ---" >> "$OUTFILE"
docker ps -a --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}" >> "$OUTFILE" 2>&1 || true
echo "" >> "$OUTFILE"

# --- docker volumes ---

echo "--- docker volume ls ---" >> "$OUTFILE"
docker volume ls >> "$OUTFILE" 2>&1 || true
echo "" >> "$OUTFILE"

echo "--- docker volume inspect (compose volumes) ---" >> "$OUTFILE"
for v in $(docker volume ls -q); do
  echo "Volume: $v" >> "$OUTFILE"
  docker volume inspect "$v" >> "$OUTFILE" 2>&1 || true
  MOUNT=$(docker volume inspect "$v" -f '{{.Mountpoint}}' 2>/dev/null || true)
  if [ -n "$MOUNT" ] && [ -d "$MOUNT" ]; then
    du -sh "$MOUNT" 2>/dev/null | awk '{print "du: "$0}' >> "$OUTFILE" || true
  fi
  echo "" >> "$OUTFILE"
done

# --- docker-compose config ---

echo "--- docker-compose config (if possible) ---" >> "$OUTFILE"
if command -v docker-compose >/dev/null 2>&1; then
  docker-compose config 2>&1 | sed -n '1,200p' >> "$OUTFILE" || true
else
  docker compose config 2>&1 | sed -n '1,200p' >> "$OUTFILE" || true
fi
echo "" >> "$OUTFILE"

# --- health endpoints ---

echo "--- Bot health endpoints ---" >> "$OUTFILE"
HEALTH_URL="http://localhost:8080/healthz"
METRICS_URL="http://localhost:8080/metrics"
echo "health: $HEALTH_URL" >> "$OUTFILE"
echo "metrics: $METRICS_URL" >> "$OUTFILE"
echo "curl health (3s timeout):" >> "$OUTFILE"
curl -sS --max-time 3 "$HEALTH_URL" 2>&1 | sed -n '1,20p' >> "$OUTFILE" || echo "health curl failed or timed out" >> "$OUTFILE"
echo "" >> "$OUTFILE"
echo "curl metrics (first 40 lines):" >> "$OUTFILE"
curl -sS --max-time 5 "$METRICS_URL" 2>&1 | sed -n '1,40p' >> "$OUTFILE" || echo "metrics curl failed or timed out" >> "$OUTFILE"
echo "" >> "$OUTFILE"

# --- logs (last lines) for key services ---

echo "--- Recent logs (last 200 lines) ---" >> "$OUTFILE"
SERVICES=(bot db minio redis test_db worker grafana)
for s in "${SERVICES[@]}"; do
  echo "--- logs: $s ---" >> "$OUTFILE"
  if docker-compose ps "$s" >/dev/null 2>&1; then
    docker-compose logs --tail=200 "$s" 2>&1 >> "$OUTFILE" || true
  else
    CN=$(docker ps --filter "name=$s" --format '{{.Names}}' | head -n1 || true)
    if [ -n "$CN" ]; then
      docker logs --tail 200 "$CN" 2>&1 >> "$OUTFILE" || true
    else
      echo "no container for $s found" >> "$OUTFILE"
    fi
  fi
  echo "" >> "$OUTFILE"
done

# --- backups check ---

echo "--- Backups folder ---" >> "$OUTFILE"
BACKUP_DIR="./backups"
if [ -d "$BACKUP_DIR" ]; then
  echo "Backups dir: $BACKUP_DIR" >> "$OUTFILE"
  ls -lAh "$BACKUP_DIR" 2>&1 >> "$OUTFILE" || true
  echo "" >> "$OUTFILE"
  LATEST=$(ls -1t "$BACKUP_DIR" 2>/dev/null | head -n1 || true)
  if [ -n "$LATEST" ]; then
    echo "Latest backup: $LATEST" >> "$OUTFILE"
    stat -c '%y %s' "$BACKUP_DIR/$LATEST" 2>/dev/null >> "$OUTFILE" || true
  else
    echo "No backups found in $BACKUP_DIR" >> "$OUTFILE"
  fi
else
  echo "Backups dir not present at $BACKUP_DIR" >> "$OUTFILE"
fi
echo "" >> "$OUTFILE"

# --- Postgres quick check ---

echo "--- Postgres quick check ---" >> "$OUTFILE"
PG_CN=$(docker ps --filter "name=db" --format '{{.Names}}' | head -n1 || true)
if [ -n "$PG_CN" ]; then
  echo "Postgres container: $PG_CN" >> "$OUTFILE"
  docker exec -i "$PG_CN" bash -lc "psql -Atc 'SELECT datname FROM pg_database;' -U saasuser" >> "$OUTFILE" 2>&1 || echo "psql query failed or DB not ready" >> "$OUTFILE"
fi
echo "" >> "$OUTFILE"

# --- Hawk (error tracking) diagnostics ---

echo "--- Hawk (error tracking) diagnostics ---" >> "$OUTFILE"
BOT_CN=$(docker ps --filter "name=bot" --format '{{.Names}}' | head -n1 || true)
if [ -n "$BOT_CN" ]; then
  echo "Bot container: $BOT_CN" >> "$OUTFILE"
  echo "BOT env vars (BOT_TOKEN/HAWK_TOKEN) inside container:" >> "$OUTFILE"
  docker exec -i "$BOT_CN" env | grep -E 'BOT_TOKEN|HAWK_TOKEN' 2>/dev/null >> "$OUTFILE" || true
  echo "" >> "$OUTFILE"
  echo "checking python hawkcatcher module inside bot container (dir listing / attr list):" >> "$OUTFILE"

  # Проверяем наличие python или python3 внутри контейнера
  if docker exec -i "$BOT_CN" sh -c 'command -v python >/dev/null 2>&1 || command -v python3 >/dev/null 2>&1'; then
    docker exec -i "$BOT_CN" sh -c 'command -v python >/dev/null 2>&1 && python - || python3 -' <<'PY' 2>/dev/null
try:
    import hawkcatcher, inspect
    names = [n for n in dir(hawkcatcher) if not n.startswith("_")]
    print("hawkcatcher exports:", names[:40])
    if hasattr(hawkcatcher, "send_event"):
        print("send_event exists")
    else:
        print("send_event NOT FOUND")
except Exception as e:
    print("import error:", type(e).__name__, e)
PY
  else
    echo "No python or python3 interpreter found in container $BOT_CN" >> "$OUTFILE"
  fi
  echo "" >> "$OUTFILE"
else
  echo "Bot container not running — skip hawk check" >> "$OUTFILE"
fi
echo "" >> "$OUTFILE"


# --- Disk usage (host) ---

echo "--- Disk usage (host) ---" >> "$OUTFILE"
if command -v df >/dev/null 2>&1; then
  df -h >> "$OUTFILE" 2>&1 || true
fi
echo "" >> "$OUTFILE"

# --- Summary Suggestions ---

echo "--- Summary Suggestions ---" >> "$OUTFILE"
echo "Check the following in order if any statuses are not healthy:" >> "$OUTFILE"
echo "1) MinIO marked unhealthy -> check free disk on host & MinIO volume." >> "$OUTFILE"
echo "2) If Postgres errors like 'No space left' -> investigate docker volume saas_bot_postgres_data and free host disk." >> "$OUTFILE"
echo "3) Hawk send_event missing -> check hawkcatcher version inside bot image; run 'docker exec -it <bot> python -c \"import hawkcatcher; print(dir(hawkcatcher))\"' and inspect requirements.txt" >> "$OUTFILE"
echo "4) Backups: ensure backup script exists in /backups inside backup container and that host mounted backups folder is writable." >> "$OUTFILE"
echo "" >> "$OUTFILE"

echo "" >> "$OUTFILE"
echo "Report saved to $OUTFILE"
echo "--- short summary ---"
tail -n 30 "$OUTFILE"

exit 0
