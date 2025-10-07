
# 🚀 Project Documentation


> ⚙️ **Архитектура:** FastAPI + PostgreSQL + Redis + MinIO  
> 🧪 **Тесты:** pytest + Alembic + Docker Compose  
> 🧰 **CI/CD:** GitHub Actions с unit + smoke тестами  
> 🧱 **Деплой:** через Docker image (production-ready)


Добро пожаловать!  
Этот проект — backend-сервис для управления компаниями, пользователями, проектами, задачами, файлами и подписками.  

Документация 1сделана так, чтобы разработчик (даже новичок) мог **поднять проект за 10 минут** и быстро разобраться в архитектуре.  

---

## 📑 Оглавление
- [🚀 Запуск проекта](#-запуск-проекта)
- [🗄️ Архитектура сервисов](#️-архитектура-сервисов)
- [🧩 Архитектура окружений](#-архитектура-окружений)
- [🧭 Схема подключения окружений](#-схема-подключения-окружений)
- [📌 Проверка окружений](#-проверка-окружения)  
- [📊 ER-диаграмма базы](#-er-диаграмма-базы)
- [🔐 Роли и доступы](#-роли-и-доступы)
- [💳 Подписки и биллинг](#-подписки-и-биллинг)
- [📌 Полезные команды](#-полезные-команды)
- [🛠️ Деплой чеклист](#️-деплой-чеклист)
- [📘 CI/CD Pipeline](#-ci-cd-pipeline)
- [⚡ Миграции (Alembic)](#-миграции-alembic)
- [🐋 Конфигурация PostgreSQL](#-конфигурация-postgresql)  
- [📚 Дополнительная документация](#-дополнительная-документация)


---

## 🚀 Запуск проекта

```bash
# Клонируем репозиторий
git clone <repo_url>
cd <repo_name>

# Настраиваем окружение
cp .env.example .env

# Сборка и запуск
make build
make up
````

После старта сервис будет доступен по адресу:
👉 [http://localhost:8000](http://localhost:8000)

---

## 🗄️ Архитектура сервисов

* **FastAPI** — основной backend
* **PostgreSQL** — база данных
* **Alembic** — миграции
* **Docker + docker-compose** — инфраструктура
* **S3-хранилище** — файлы и вложения
* **JWT + refresh-токены** — авторизация

```mermaid
flowchart TD
    Client --> API
    API --> DB[(PostgreSQL)]
    API --> Storage[(S3 Bucket)]
    API --> Auth[(JWT / Sessions)]
```


---


## 🧩 Архитектура окружений и взаимодействие сервисов

Проект разделён на изолированные окружения:

| Окружение | Назначение | Описание |
|------------|-------------|----------|
| **Local** | Разработка | Работает через `docker compose`, использует `.env` |
| **Test** | Локальные тесты и CI | Использует `.env.test` и временную базу `saasdb_test` |
| **CI/CD** | GitHub Actions | Поднимает окружение через Docker Compose и выполняет smoke-тесты |
| **Production** | Продакшен | Использует `.env.production` или переменные окружения из секрета |

---

### 🧠 Логика взаимодействия компонентов

```mermaid
flowchart TD
    subgraph App_Container["🧩 saas_bot (FastAPI / aiogram)"]
      BOT -->|asyncpg| POSTGRES[(PostgreSQL main)]
      BOT -->|redis-py| REDIS[(Redis cache)]
      BOT -->|boto3| MINIO[(S3 MinIO)]
      BOT -->|psycopg2| ALEMBIC[(Alembic migrations)]
      BOT -->|pytest| TEST_DB[(PostgreSQL test)]
    end

    subgraph CI_Pipeline["⚙️ GitHub Actions CI"]
      LINT[Lint / Security] --> UNIT[Unit Tests]
      UNIT --> BUILD[Docker Build]
      BUILD --> SMOKE[Smoke Tests]
    end

    SMOKE --> App_Container
    SMOKE --> POSTGRES
    SMOKE --> REDIS
    SMOKE --> MINIO
```

---

### ⚙️ Принцип работы локально

1. **Docker Compose** поднимает контейнеры:
   - `bot` — приложение
   - `db` — основная база PostgreSQL
   - `test_db` — тестовая база
   - `redis` — кэш
   - `minio` — S3-хранилище для файлов

2. **Переменные окружения** загружаются из `.env` и `.env.test`.

3. **Миграции** применяются внутри контейнера `bot` командой:
   ```bash
   docker compose run --rm bot alembic upgrade head
   ```

4. **Тесты** используют отдельную тестовую базу `saasdb_test`, чтобы не затронуть продовые данные.

---

### 🧪 Принцип работы в CI (GitHub Actions)

1. **Lint / Security** — проверяет стиль и уязвимости.  
2. **Unit Tests** — запускает тесты на чистом контейнере Postgres.  
3. **Docker Build** — собирает итоговый образ, который потом пойдёт в продакшен.  
4. **Smoke Tests** — запускает `docker compose` внутри CI, применяет миграции и проверяет, что образ реально работает.  

> 💡 Отчёты о тестах (HTML + JUnit XML) сохраняются в артефакты GitHub Actions.

---

### 🧱 Надёжность и масштабируемость

| Критерий | Оценка | Обоснование |
|-----------|--------|--------------|
| Изоляция окружений | ✅ | `.env`, `.env.test`, `.env.ci` полностью независимы |
| Повторяемость сборок | ✅ | Все стадии CI используют одни и те же Docker-контейнеры |
| Миграции | ✅ | Alembic централизован, синхронный и управляется через контейнер |
| Масштабирование | ✅ | Переход на Kubernetes возможен без изменений кода |
| Централизация настроек | ⚙️ Почти | Можно вынести общие переменные в `.env.shared` |
| Отладка и тестирование | ✅ | `pytest` и `smoke-tests` дают полный цикл проверки |

---

### 📂 Связанные файлы

| Файл | Назначение |
|------|-------------|
| `.env` | локальные переменные для `docker-compose` |
| `.env.test` | настройки тестовой базы |
| `.env.ci` | окружение CI/CD |
| `docker-compose.yml` | инфраструктура (db, redis, minio, bot) |
| `.github/workflows/ci.yml` | пайплайн GitHub Actions |
| `Dockerfile` | сборка финального образа |
| `alembic.ini` / `migrations/` | миграции базы данных |



---


### 🧭 Схема подключения окружений

```mermaid
flowchart TD
    subgraph Dev["🧩 Local Development"]
        BOT_DEV["bot (FastAPI)"] --> DB_DEV["PostgreSQL (db:5432)"]
        BOT_DEV --> REDIS["Redis"]
        BOT_DEV --> MINIO["MinIO (S3)"]
    end

    subgraph Tests["🧪 Local Tests / CI"]
        PYTEST["pytest"] --> TEST_DB["PostgreSQL (test_db:5432, tmpfs)"]
        PYTEST --> REDIS
        PYTEST --> MINIO
    end

    subgraph CI["⚙️ GitHub Actions CI/CD"]
        LINT["Lint & Security"] --> UNIT["Unit Tests (localhost DB)"]
        UNIT --> BUILD["Docker Build"]
        BUILD --> SMOKE["Smoke Tests (docker compose)"]
    end

    CI --> Tests
    CI --> Dev
```

#### 🔹 Dev (разработка)

* База: `db:5432`
* Конфиг: `.env`
* Контейнеры: `bot`, `worker`, `db`, `redis`, `minio`

#### 🔹 Test (pytest)

* База: `test_db:5432`
* Конфиг: `.env.test`
* Данные не сохраняются (`tmpfs`)

#### 🔹 CI/CD (GitHub Actions)

* Линт, юнит-тесты, smoke-тесты
* Переменные окружения подгружаются из `.env.ci`
* Финальный Docker-образ проверяется на запуск




---

## 🧱 Проверка окружений

Этот раздел помогает убедиться, что каждое окружение работает корректно и изолированно.
Следующие команды можно выполнять локально, в контейнерах или в CI.


### 🔹 1. Проверка dev-окружения

```bash
# Пересобрать и поднять окружение разработки
make build
make up

# Проверить подключение к dev-базе
docker compose exec db psql -U saasuser -d saasdb -c '\dt'

# Проверить, что бот запущен
make logs
```

✅ Ожидаемый результат:

* контейнер `saasbot` в статусе *running*
* в логах видно `BOT_TOKEN: dummy...`
* таблицы в `saasdb` присутствуют после миграций

---

### 🔹 2. Проверка тестового окружения

```bash
# Запуск изолированных тестов с временной базой
make tloc
```

✅ Ожидаемый результат:

* база `saasdb_test` создаётся во временном контейнере `test_db`
* pytest показывает `5 passed in ...s`
* после завершения окружение очищается автоматически

> 💡 Тесты никогда не трогают dev-базу — используются переменные из `.env.test`.

---

### 🔹 3. Проверка CI/CD пайплайна локально (эмуляция)

```bash
# Проверяем, что пайплайн можно выполнить локально
act -j smoke-tests
```

> Если установлен [**nektos/act**](https://github.com/nektos/act),
> команда прогонит GitHub Actions прямо на твоей машине.

✅ Ожидаемый результат:

* проходят lint, unit, smoke тесты
* создаётся артефакт `smoke-test-results/`

---

### ⚙️ Итоговое соответствие окружений

| Тип окружения | Файл конфигурации | База данных   | Назначение                   |
| ------------- | ----------------- | ------------- | ---------------------------- |
| Local Dev     | `.env`            | `saasdb`      | Основная разработка          |
| Local Test    | `.env.test`       | `saasdb_test` | Изолированные pytest-тесты   |
| CI/CD         | `.env.ci`         | `saasdb_test` | Smoke и unit тесты в Actions |
| Production    | `.env.production` | `saasdb`      | Рабочая среда                |




---

## 📊 ER-диаграмма базы

```mermaid
erDiagram
    USERS ||--o{ TASKS : "assigned"
    USERS ||--o{ FILES : "uploaded"
    USERS ||--o{ SESSIONS : "sessions"

    COMPANIES ||--o{ USERS : "members"
    COMPANIES ||--o{ PROJECTS : "projects"
    COMPANIES ||--o{ TASKS : "tasks"
    COMPANIES ||--o{ FILES : "files"
    COMPANIES ||--o{ SUBSCRIPTIONS : "subscriptions"
    COMPANIES ||--o{ TRIALS : "trials"
    COMPANIES ||--o{ INVOICES : "invoices"

    PROJECTS ||--o{ TASKS : "tasks"
    TASKS ||--o{ FILES : "attachments"

    PLANS ||--o{ SUBSCRIPTIONS : "subscriptions"
    PLANS ||--o{ INVOICES : "invoices"
    INVOICES ||--o{ PAYMENTS : "payments"

    USERS ||--o{ AUDIT_LOGS : "actions"
```

---

## 🔐 Роли и доступы

* **Admin** — полный доступ ко всем данным и настройкам.
* **Manager** — управление проектами, пользователями компании.
* **Worker** — выполнение задач, загрузка файлов.
* **Client** — просмотр проектов и подтверждение выполненных работ.

📚 Подробнее: [docs/roles.md](docs/roles.md)

---

## 💳 Подписки и биллинг

* **Trial** — бесплатный пробный период.
* **Subscription** — платная подписка (привязка к плану).
* **Invoice** — счет компании.
* **Payment** — оплата по счету.

📚 Подробнее: [docs/db\_cascades.md](docs/db_cascades.md)

---

## 📌 Полезные команды

```bash
make build      # собрать контейнеры
make up         # запустить проект
make down       # остановить проект
make logs       # посмотреть логи
make shell      # попасть внутрь контейнера
make migrate    # применить миграции
make revision   # создать новую миграцию
```

---

## 🛠️ Деплой чеклист

* [ ] Обновить `.env`
* [ ] Применить миграции (`make migrate`)
* [ ] Проверить состояние подписок и триалов
* [ ] Проверить работу S3-хранилища
* [ ] Прогнать тесты перед релизом


---

## 📘 CI/CD Pipeline

### 🎯 Что тестируется в пайплайне

В проекте используется единый workflow **CI Pipeline**:

* **Lint**: проверка стиля и безопасности (ruff, black, flake8, bandit, safety)
* **Unit tests**: тесты в изолированном Postgres (service container), покрытие через pytest + coverage
* **Smoke tests**: базовые сценарии работы приложения

### 🔄 Конфигурация окружения

* **.env** — базовая среда для docker-compose
* **.env.local** — локальные секреты (токены, ключи)
* **.env.ci** — тестовые переменные для CI/CD




---

## ⚡ Миграции (Alembic)

В проекте используется **асинхронный Alembic** для работы с PostgreSQL.
Это гарантирует совместимость с `async SQLAlchemy` и исключает необходимость переделки схемы в будущем.

### 🔄 Изменения, которые мы внесли:

1. **Асинхронный движок**
```python
from sqlalchemy.ext.asyncio import create_async_engine
connectable = create_async_engine(
 url,
 future=True,
 echo=os.getenv("DEBUG") == "1"
)
```

2. **Разделение окружений**
* Используем `ENV=production` для продакшена
* Локально и в CI подхватываем `DATABASE_URL` / `TEST_DATABASE_URL`

3. **Логирование**
```python
logger.setLevel(logging.DEBUG if os.getenv("DEBUG") else logging.INFO)
```

4. **Обработка ошибок**
```python
try:
 asyncio.run(run_migrations_online())
except Exception as e:
 logger.critical(f"Критическая ошибка при выполнении миграций: {e}")
 raise
```

5. **alembic.ini**
В `alembic.ini` строка `sqlalchemy.url` оставлена пустой:
```ini
sqlalchemy.url =
```
URL теперь всегда берётся из переменных окружения.

---

### 📋 Как применять миграции

**Локально:**
```bash
make revision # создать новую миграцию
make migrate # применить миграции
```

**В CI:**
* Автоматически выполняются smoke-тесты и миграции
* Используется `TEST_DATABASE_URL`
* В случае ошибки миграции пайплайн падает

**В продакшене:**
```bash
ENV=production make migrate
```



---


## 🐋 Конфигурация PostgreSQL

### 📊 Окружения и базы данных

В проекте используются разные базы данных для разных окружений:

**Продакшен-окружение:**
* Основная база данных: `saasdb`
* Используется в продакшен-боте и воркере

**Тестовые окружения:**
* Тестовая база данных: `saasdb_test`
* Используется в CI и локальных тестах

### 🔄 Переменные окружения

Для всех окружений используются атомарные переменные:
* `POSTGRES_USER`
* `POSTGRES_PASSWORD`
* `POSTGRES_HOST`
* `POSTGRES_PORT`
* `POSTGRES_DB`

Такой подход:
* Устраняет дублирование настроек
* Исключает расхождения между `DATABASE_URL` и `TEST_DATABASE_URL`
* Делает конфигурацию более прозрачной

### 📋 Примеры конфигураций

**Локальная разработка** (.env.local):
```env
POSTGRES_USER=saasuser
POSTGRES_PASSWORD=saaspass
POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_DB=saasdb




---




## 📚 Дополнительная документация

* [Роли и доступы](docs/roles.md)
* [Каскады и удаление](docs/db_cascades.md)
* [Чеклист каскадов (ручная проверка)](docs/db_cascades_checklist.md)  
* [Миграции и CI/CD](docs/migrations.md)
* [Runbook — эксплуатация бота](docs/runbook.md)

---
# test CI trigger
