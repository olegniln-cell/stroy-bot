Поясню подробно, что у тебя сейчас происходит и как это работает, чтобы ты чувствовал всю схему инфраструктуры, а не просто файлы.

🧠 1. Dev база (db:)

Да — это основная база данных для разработки (dev).
Она определяется вот этим блоком:

  db:
    image: postgres:15
    container_name: saasbot_db
    restart: unless-stopped
    env_file:
      - .env
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-saasdb}
      POSTGRES_USER: ${POSTGRES_USER:-saasuser}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-saaspass}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

⚙️ Что это значит:

postgres_data — постоянное хранилище на диске.
Даже если контейнер перезапустишь — данные сохранятся.

5432:5432 — база доступна и извне (например, IDE, pgAdmin).

.env загружает POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD.

Это база, куда подключается бот и воркер в деве.

🧪 2. Тестовая база (test_db:)

Да — вторая база, специально для тестов.
Она изолирована, работает в том же Docker network,
но на другом порту и не использует постоянный volume.

  test_db:
    image: postgres:15
    container_name: saasbot_test_db
    env_file:
      - .env.test
    ports:
      - "5433:5432"
    tmpfs:
      - /var/lib/postgresql/data

⚙️ Что это значит:

tmpfs — данные хранятся в оперативке и стираются после остановки контейнера.
→ идеально для юнит-тестов.

Порт 5433 внешне, но в сети сервис доступен по имени test_db:5432.

Файл .env.test гарантирует, что там другой DATABASE_URL.

💡 Важно:
Когда тесты запускаются, pytest берёт DATABASE_URL из .env.test,
и должен подключаться к test_db.
Проблема была в том, что тесты брали .env, а не .env.test.

🤖 3. Контейнеры-приложения
🟢 bot
  bot:
    build: .
    depends_on:
      db:
        condition: service_healthy


— Это сам FastAPI-приложение (бот), которое общается с dev-базой (db).

🧱 worker
  worker:
    build: .
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started


— Фоновый процесс.
Он, например, может:

обрабатывать очереди задач (через Redis),

синхронизировать файлы с MinIO,

выполнять асинхронные события, чтобы бот не зависал.

Обычно воркер запускает ту же бизнес-логику, но без API — просто воркер-процессы.

💾 4. Redis

Классический брокер для хранения временных данных и очередей.
FastAPI-бот может класть туда задачи, а worker их вытаскивает.
Также Redis может использоваться для:

кэширования

rate limiting (ограничение запросов)

хранения user-сессий

☁️ 5. MinIO

Это self-hosted аналог Amazon S3.
Ты его используешь для хранения файлов (документов, отчётов и т.д.).
В твоём коде, скорее всего, есть что-то вроде:

import boto3
s3 = boto3.client(
    "s3",
    endpoint_url="http://minio:9000",
    aws_access_key_id="minioadmin",
    aws_secret_access_key="minioadmin",
)

🧩 В итоге у тебя сейчас схема такая:
                   ┌──────────────┐
                   │  Telegram    │
                   └──────┬───────┘
                          │
                          ▼
                  ┌──────────────┐
                  │  bot (FastAPI)│
                  └──────┬───────┘
                         │
             ┌───────────┴────────────┐
             ▼                        ▼
       ┌────────────┐           ┌─────────────┐
       │ PostgreSQL │<──vol───>│ Redis        │
       │ saasdb     │          │ queue/cache  │
       └────────────┘           └─────────────┘
             │
             ▼
        ┌────────────┐
        │   MinIO    │
        └────────────┘


А при тестах:

pytest ──> test_db (saasdb_test, временная база в RAM)
