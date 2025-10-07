💯 Отлично, вот это правильное направление — ты уже стабилизировал инфраструктуру, CI почти готов, значит самое время перейти к **фундаменту (Фаза 2)**.
Давай зафиксируем понятную дорожную карту, чтобы завтра ты мог взять её как чек-лист.

---

## 🧱 **ФАЗА 2 — Минимальный костяк стабильности**

> Цель: превратить проект из «просто работает» → в надёжную систему, где можно безопасно дебажить, собирать метрики и восстанавливаться после ошибок.

---

### ✅ **1. Логирование (структурное и трассируемое)**

**Задача:** заменить `logging` → на `structlog` (или `loguru`, но structlog гибче под JSON и OpenTelemetry).

**Добавить файл:** `core/logging_setup.py`

```python
import structlog
import logging
import sys

def setup_logging():
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        cache_logger_on_first_use=True,
    )

logger = structlog.get_logger()
```

**Использование в коде:**

```python
from core.logging_setup import logger

logger.info("user_login", user_id=user.id, ip=request.client.host)
```

➡️ **Плюсы:**

* красиво форматированный JSON в `docker logs`;
* легко фильтровать в Sentry/ELK;
* можно добавить `request_id`, `user_id`, `company_id` как контекст.

---

### ✅ **2. Error tracking (Sentry)**

**Установка:**

```bash
pip install sentry-sdk[fastapi]
```

**Добавь в `main.py`:**

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

if dsn := os.getenv("SENTRY_DSN"):
    sentry_sdk.init(
        dsn=dsn,
        integrations=[FastApiIntegration()],
        traces_sample_rate=0.2,  # 20% запросов для трейсинга
    )
```

**Добавь переменную в `.env.local`:**

```
SENTRY_DSN=<твоя ссылка из Sentry>
```

---

### ✅ **3. Метрики (Prometheus)**

**Установка:**

```bash
pip install prometheus-client
```

**Добавь endpoint `/metrics`:**

```python
from fastapi import FastAPI, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
```

**Пример метрики:**

```python
from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter("requests_total", "Total requests", ["method", "endpoint"])
REQUEST_LATENCY = Histogram("requests_latency_seconds", "Request latency", ["endpoint"])
```

и в middleware:

```python
@app.middleware("http")
async def metrics_middleware(request, call_next):
    import time
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    REQUEST_COUNT.labels(request.method, request.url.path).inc()
    REQUEST_LATENCY.labels(request.url.path).observe(duration)
    return response
```

---

### ✅ **4. Бэкапы БД**

**Простой локальный cron job:**
создай `scripts/backup_db.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

DATE=$(date +%Y%m%d_%H%M%S)
DUMP_FILE="/backups/saasdb_$DATE.sql"

echo "📦 Dumping database..."
pg_dump -h db -U saasuser saasdb > "$DUMP_FILE"
echo "✅ Backup saved to $DUMP_FILE"
```

и в `docker-compose.yml` можно добавить job:

```yaml
  backup:
    image: postgres:15
    volumes:
      - ./backups:/backups
    entrypoint: ["/bin/sh", "-c", "while true; do /backups/backup_db.sh; sleep 86400; done"]
```

---

### ✅ **5. Runbook / Инцидент-план**

Создай `/docs/runbook.md`:

````markdown
# 🧭 Runbook (инцидент-план)

## 🔴 Если бот упал
```bash
docker compose logs bot -n 50
docker compose restart bot
````

## 🟡 Если база не отвечает

```bash
docker compose exec db psql -U saasuser -d saasdb -c '\l'
```

## 🟠 Если тесты падают

Проверь `.env.test` и `DATABASE_URL`.

## 🟢 Если нужно откатить

1. Найди нужный dump в `backups/`.
2. Восстанови:

   ```bash
   psql -h db -U saasuser -d saasdb < backups/saasdb_<DATE>.sql
   ```

```

---

## 🚀 **Что делать сейчас, пока GitHub недоступен**

✅ **Шаг 1.** Создай файлы локально:
- `core/logging_setup.py`
- `scripts/backup_db.sh`
- `docs/runbook.md`

✅ **Шаг 2.** Добавь импорт логгера и Sentry в `main.py`.

✅ **Шаг 3.** Добавь `/metrics` в `main.py`.

✅ **Шаг 4.** Прогони `make up` и проверь:
- `/metrics` работает;
- логи красиво в JSON;
- ошибки в Sentry приходят.

---

Хочешь, я соберу всё это в один аккуратный commit-пакет (`feat: observability core — logging + sentry + metrics + runbook`) и покажу точный diff, который можно будет просто применить у себя?
```
