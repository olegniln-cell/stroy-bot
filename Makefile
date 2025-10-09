# ===============================
# 📌 Makefile для управления проектом saas_bot
# ===============================

# 🟢 Указываем, что все цели — «фальшивые», а не имена файлов
.PHONY: help \
        up down stop restart build rebuild logs \
        migrate current reset fresh \
        psql testpsql \
        seed ch_seed check-fk check_models tenum \
        test

# ===============================
# 🔹 Основная помощь
# ===============================
help:
	@echo ""
	@echo "🚀 Доступные команды:"
	@echo ""
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""



# ===============================
# 🔹 Управление сервисами
# ===============================


upbb: ## пересборка быстрая
	docker compose build bot

up: ## Запустить все сервисы (бот, БД, Redis, MinIO) в фоне
	docker-compose up -d

upup: ## Запустить все сервисы (бот, БД, Redis, MinIO) в фоне
	docker-compose up -d --build bot

up2: ##пересборка и запуск
	docker-compose up --build bot

ups: ## Пересобрать и сразу запустить все сервисы
	docker-compose up --build -d

upc: ## Пересобрать c нуля удаление кеша
	docker-compose build --no-cache


uptt: ## простройка образа с нуля если вдруг что -то осталось в кеше
	docker compose -f docker-compose.test.yml build --no-cache bot


upb: ## Пересобрать и запустить только bot
	docker-compose up --build -d bot

upcb: ## Пересобрка занова с очисткой кеша
	docker compose build --no-cache bot


down: ## Остановить и удалить все контейнеры
	docker-compose down

stop: ## Остановить контейнеры (без удаления)
	docker-compose stop

restart: ## Полный рестарт: остановить и запустить заново с пересборкой
	docker-compose down
	docker-compose up --build -d

logs: ## Показать логи сервиса bot в реальном времени
	docker-compose logs -f bot

cbd: ## Бекап базы в корень
	docker-compose exec db pg_dump -U saasuser saasdb > backup.sql

cf: ## копирование всех файлов
	python3 merge_code.py



# ===============================
# 🔹  СМОК ТЕСТЫ В CI
# ===============================

cor: ## только core
	pytest -m smoke_core -v

bil: ## только билинг
	docker compose run --rm bot pytest -vv tests/smoke/test_billing_flow.py


fil: ## только файлы
	pytest -m smoke_files -v

vt: ## все
	pytest -m smoke -v

bpy: ##
	docker compose run --rm bot pytest -m smoke -v








# ===============================
# 🔹  Архитектура (docker-compose)
# ===============================

sk: ## список контейнеров
	docker ps

vs: ## сеть docker-compose. Обычно docker-compose создаёт сеть с названием <project>_default.
	docker network ls

kc: ## Узнать, какие контейнеры сидят в сети Containers — список контейнеров, подключённых к сети
## Их IP и имена (именно эти имена используются в DATABASE_URL, например saasbot_test_db)
	docker network inspect saas_bot_default




# ===============================
# 🔹 Сборка
# ===============================
build: ## Пересобрать образы без запуска
	docker-compose build

rebuild: ## Пересобрать и сразу запустить все сервисы
	docker-compose up --build -d




# ===============================
# 🔹 Миграции и база данных
# ===============================
mig: ## Применить все миграции (alembic upgrade head)
	docker-compose run --rm bot alembic upgrade head

current: ## Показать текущую версию миграций
	docker-compose run --rm bot alembic current


reset1: ## Полный сброс окружения: удалить контейнеры и тома, заново применить миграции
	docker-compose down -v
	docker-compose up -d db test_db
	sleep 5
	docker-compose run --rm bot alembic upgrade head
	# применяем миграции к тестовой БД
	docker-compose run --rm bot alembic -x db_url=postgresql+psycopg2://saasuser:saaspass@saasbot_test_db:5432/saasdb_test upgrade head


reset: ## Полный сброс окружения: удалить контейнеры и тома, заново применить миграции
	docker-compose down -v
	docker-compose up -d db
	sleep 5
	docker-compose run --rm bot alembic upgrade head

fresh: ## Запустить с нуля (сборка, миграции, запуск bot и worker)
	docker-compose down -v
	docker-compose up --build -d db redis minio
	sleep 5
	docker-compose run --rm bot alembic upgrade head
	docker-compose up -d bot worker

psql: ## Подключиться к базе данных через psql
	docker-compose exec db psql -U saasuser -d saasdb

testpsql: ## Подключиться к тестовой базе данных через psql
	docker exec -it saasbot_test_db psql -U saasuser -d saasdb_test

midtestbaz: ## миграции для тестововй базы
	SYNC_DATABASE_URL="postgresql+psycopg2://saasuser:saaspass@localhost:5433/saasdb_test" \
alembic upgrade head

tb: ## накатка миграции на тестовую базу
	docker compose run --rm bot alembic upgrade head











# ===============================
# 🔹 Данные
# ===============================
seed: ## Заполнить БД начальными данными
	docker-compose exec bot python -m scripts.seed

ch_seed: ## Проверить, что начальные данные загружены
	docker-compose exec bot python -m scripts.check_seed



# ===============================
# 🔹 Диагностика
# ===============================
check-fk: ## Проверить битые внешние ключи (FK) в БД
	docker-compose exec -T db psql -U saasuser -d saasdb < scripts/check_fk_safe.sql

chmod: ## Проверить, что модели Python совпадают с таблицами в БД
	docker-compose exec bot python scripts/check_models_vs_db.py





# ===============================
# 🔹 Тесты
# ===============================



test1: ## Запустить pytest внутри контейнер
	docker exec -e SYNC_TEST_DATABASE_URL=postgresql+psycopg2://saasuser:saaspass@db:5432/saasdb_test \
	           -e ASYNC_TEST_DATABASE_URL=postgresql+asyncpg://saasuser:saaspass@db:5432/saasdb_test \
	           -it saasbot python -m pytest -v

testf: ##  быстрая проверка теста локально
	RESET_DB=false pytest -v -m smoke

tenum: ## Проверить синхронизацию enum (pytest для enums)
	docker-compose exec bot pytest -q tests/test_enum_sync.py



tfile: ## тест работы загрузки файлов
	docker compose run --rm bot python -m scripts.test_s3

clean-s3: ##  Очистка bucket, удаляет ВСЕ объекты
	docker compose run --rm bot python -m scripts.clear_s3

	docker compose run --rm bot python -m scripts.test_cascades.py
	pytest -q tests/test_cascades.py


clean-s3-keep: ##  Очистка bucket, но сохраняет папку uploads/
	docker compose run --rm bot python -m scripts.clear_s3 --keep-uploads

tc: ##  Прооверка каскадов и soft delete
	docker compose run --rm bot pytest -s tests/test_cascades.py

tc2: ##  Прооверка каскадов и soft delete
	docker compose run --rm bot pytest -v tests/test_cascade_relations.py

t:  ## прогнать все тесты
	docker compose run --rm bot pytest -s

taudit: ## тест аудита черного ящика ручной скрипт
	docker compose run --rm bot pytest -s tests/test_audit_log.py


check-cascades:
	psql "$${DB_URL}" -f docs/db_cascades.sql

st: ## smoke_tests
	pytest -m smoke -v

st1: ## smoke_tests
	docker compose run --rm bot /bin/sh -c \"export TEST_DATABASE_URL='postgresql+asyncpg://saasuser:saaspass@test_db:5432/saasdb_test' && \pytest tests/integration/smoke_tests.py -m smoke -v




# ===============================
# 🔹  фикс
# ===============================
rch: ## проверить фиксы
	ruff check .

 fix: ## чистка фисов
	ruff check . --fix

bch: ## проверка
	black .

ich: ## проверка
	isort .









clean: ## очистка файлов с гетлаба
	@echo "🧹 Cleaning up Python cache and build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	rm -rf build/ dist/ *.egg-info .pytest_cache .coverage htmlcov


delci: ## Удалить все .файл файлы
	find . -name ".DS_Store" -type f -delete


# ===============================
# 🔹    Информация о контейнерах
# ===============================

cont1: ##  статус текущих контейнеров
	docker compose ps

cont2: ##  или так
	docker ps

conf1: ##  проверка конфигурации
	docker compose config



# ===============================
# 🔹 Runner (GitFlic CI/CD Agent)
# ===============================

REG_URL=https://coordinator.gitflic.ru/-/runner/registration
REG_TOKEN=7fb3dc42-5653-40a3-a3c7-201a0c338104
CONTAINER_NAME=gitflic-runner
IMAGE=registry.gitflic.ru/company/gitflic/runner:latest

runner-up: ## Запустить раннер
	docker run -d --name $(CONTAINER_NAME) \
			--restart always \
			-e REG_URL="$(REG_URL)" \
			-e REG_TOKEN="$(REG_TOKEN)" \
			-v /var/run/docker.sock:/var/run/docker.sock \
			$(IMAGE)

runner-down: ## Остановить и удалить раннер
	docker rm -f $(CONTAINER_NAME) || true

runner-logs: ## Смотреть логи раннера
	docker logs -f $(CONTAINER_NAME)

runner-status: ## Проверить статус раннера
	docker ps | grep $(CONTAINER_NAME) || true

runner-restart: ## Перезапустить раннер
	$(MAKE) runner-down
	$(MAKE) runner-up


# ===============================
# 🔹  Работа с тестовой базой
# ===============================

# Docker Compose файл для юнит-тестов
UNIT_COMPOSE = docker-compose -f docker/docker-compose.unit.yml
TEST_DB_CONTAINER = docker-saasbot_test_db-1
DB_USER = saasuser
DB_NAME = saasdb_test
BACKUP_FILE = saasdb_test_backup.sql

## 🚀 Поднять тестовую базу в фоне -3
db-up:
	$(UNIT_COMPOSE) up -d saasbot_test_db

## 🛑 Остановить тестовую базу
db-stop:
	$(UNIT_COMPOSE) stop saasbot_test_db

## ❌ Полностью удалить контейнер тестовой базы (данные внутри будут потеряны!) -2
db-rm:
	$(UNIT_COMPOSE) rm -f saasbot_test_db

## 💾 Сделать дамп (бэкап) тестовой базы в файл $(BACKUP_FILE) -1
db-backup:
	docker exec -t $(TEST_DB_CONTAINER) pg_dump -U $(DB_USER) $(DB_NAME) > $(BACKUP_FILE)

## ♻️ Восстановить базу из дампа $(BACKUP_FILE) -4
db-restore:
	cat $(BACKUP_FILE) | docker exec -i $(TEST_DB_CONTAINER) psql -U $(DB_USER) -d $(DB_NAME)

## 🐚 Подключиться к тестовой базе через psql
db-psql:
	docker exec -it $(TEST_DB_CONTAINER) psql -U $(DB_USER) -d $(DB_NAME)

## 🔄 Пересоздать тестовую базу с нуля (rm → up)
db-recreate:
	db-rm db-up

## 🔄 имена контейнеров
nemebd:
	docker ps --format "table {{.Names}}\t{{.Status}}"


unitt: #юнит тесты проверка локально
	docker compose -f docker/docker-compose.unit.yml up --build tests

integrt: #смоок - интеграционные тесты проверка локально
	docker compose -f docker/docker-compose.integration.yml up --build --abort-on-container-exit



# ===============================
# 🔹 CI / Полный прогон тестов - это можно удалить
# ===============================
citest: ## Полный прогон CI: поднимаем контейнеры, миграции, прогон тестов, остановка
	@echo "🚀 Поднимаем тестовое окружение..."
	docker-compose up -d db test_db redis minio
	@sleep 5  # ждём, пока БД и MinIO будут готовы
	@echo "🛠 Применяем миграции..."
	docker-compose run --rm --service-ports bot alembic upgrade head
	docker-compose run --rm --service-ports bot alembic -x db_url=postgresql+asyncpg://saasuser:saaspass@test_db:5432/saasdb_test upgrade head
	@echo "🧪 Запускаем интеграционные тесты..."
	docker-compose run --rm --service-ports bot pytest -v
	@echo "🧹 Завершаем окружение..."
	docker-compose down -v

citest2:
	@echo "🚀 Поднимаем тестовое окружение..."
	docker-compose up -d db test_db redis minio
	@echo "🧹 Чистим тестовую базу..."
	docker exec -i saasbot_test_db psql -U saasuser -d saasdb_test -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
	@echo "🛠 Применяем миграции..."
	docker-compose run --rm --service-ports bot alembic upgrade head
	@echo "🧪 Запускаем тесты..."
	docker-compose run --rm bot pytest -vv

citest3:
	@echo "🚀 Поднимаем тестовое окружение..."
	docker-compose up -d db test_db redis minio
	@sleep 5
	@echo "🧹 Чистим тестовую базу..."
	docker exec -i saasbot_test_db psql -U saasuser -d saasdb_test -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
	@echo "🛠 Запускаем pytest..."
	docker-compose run --rm bot pytest -vv tests/smoke --log-cli-level=INFO

pyt:
	pytest -vv

tdoc:
	docker compose -f docker-compose.test.yml run --rm bot pytest -v

tloc: ## Run isolated test suite
	./scripts/run_tests.sh


# ===============================
# 🔹 CI / отладка тестов локально
# ===============================

test-local: ## Run isolated test suite
	./scripts/run_tests.sh



# ===============================
# 🔹 Git ветки
# ===============================
blist: ## Показать все ветки
	git branch -a

branch-new: ## Создать новую ветку (пример: make branch-new name=fix/feature)
	@if [ -z "$(name)" ]; then \
		echo "❌ Нужно указать имя ветки, пример:"; \
		echo "   make branch-new name=fix/feature"; \
		exit 1; \
	fi
	git checkout -b $(name)

branch-switch: ## Переключиться на существующую ветку (пример: make branch-switch name=main)
	@if [ -z "$(name)" ]; then	 \
		echo "❌ Нужно указать имя ветки, пример:"; \
		echo "   make branch-switch name=main"; \
		exit 1; \
	fi
	git checkout $(name)

branch-delete: ## Удалить локальную ветку (пример: make branch-delete name=fix/old)
	@if [ -z "$(name)" ]; then \
		echo "❌ Нужно указать имя ветки, пример:"; \
		echo "   make branch-delete name=fix/old"; \
		exit 1; \
	fi
	git branch -d $(name)

branch-push: ## Запушить текущую ветку на remote (пример: make branch-push name=fix/feature)
	@if [ -z "$(name)" ]; then \
		echo "❌ Нужно указать имя ветки, пример:"; \
		echo "   make branch-push name=fix/feature"; \
		exit 1; \
	fi
	git push origin $(name)

branch-merge: ## Влить указанную ветку в текущую (пример: make branch-merge name=fix/feature)
	@if [ -z "$(name)" ]; then \
		echo "❌ Нужно указать имя ветки, пример:"; \
		echo "   make branch-merge name=fix/feature"; \
		exit 1; \
	fi
	git merge $(name)

branch-status: ## Проверить статус текущей ветки
	git status

checkv: ##   поменять ветку
	git checkout main



# ===============================
# 🔹  CI
# ===============================

stat: ## Проверяем статус git
	git status

add: ## Добавляем все изменения в индекс
	git add .

com: ## Коммитим изменения (пример: make com m="fix: ci config")
	@if [ -z "$(m)" ]; then \
		echo "❌ Нужно указать сообщение, пример:"; \
		echo "   make com m=\"fix: ci config\""; \
		exit 1; \
	fi
	git commit -m "$(m)"


c2: ## Коммитим в ветку
	git commit -m "fix(ci): update postgres host for CI tests"


puch: ## Пушим изменения в main
	git push origin main

p2: ## Пушим в ветку
	git push origin feature/observability

pvm: ## Переключишься на main
	git checkout main

civet: ## добавить новую ветку
	git checkout -b feature/observability

punv: ## пуш новой ветки в гитхаб
	git push -u origin feature/observability


delvet: ## Удалится ненужная ветка (уже влитая)
	git branch -d ci/unit-tests-fix


ydi: ## удалить файл из индекса
	git rm --cached migrations/versions/имя-файла.py
ydf: ## удалить файл локально
	rm migrations/versions/имя-файла.py


testbazaud: ## удаление базы тестовой и таблиц и создание новой
	docker exec -it saasbot_test_db psql -U saasuser -d saasdb_test -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

migrvtbaz: ## применение миграции в тестовой
	docker-compose run --rm bot alembic upgrade head

remgit: ## проверка какой сейчас - переключение между репозиториями
	git remote -v

remgit2: ##  включение другого
	git remote set-url origin https://github.com/sagrador/saasboot.git


.PHONY: format lint

form:
	black .
	ruff check --fix .
	flake8 .

lint:
	ruff check .
	black --check .
	flake8 .


# ===============================
# 🔹  отладка тестовой базы и базы си
# ===============================

dcom: ##   останвока ктейнерво
	docker compose down -v

dct: ##     только запуск контейнера для тестов
	docker compose up -d test_db

pcon: ##   проверка поднялся ли
	docker compose ps




# ===============================
# 🔹 Чтобы безопасно чистить docker-мусор
# ===============================


clean-docker: ## безопасная очистка docker
	@echo "🧹 Cleaning up unused Docker resources (safe mode)..."
	@docker system prune -f
	@docker volume prune -f --filter "label=temporary=true" || true
	@echo "✅ Docker cleanup complete."


clean-docker-hard: ## если хочешь ПОЛНУЮ очистку (с подтверждением)
	@echo "⚠️ WARNING: This will remove ALL images, volumes, and caches!"
	@read -p "Type 'yes' to continue: " confirm && [ "$$confirm" = "yes" ] && docker system prune -a --volumes

# ===============================
# 🔹 Чтобы Docker не “жрал” 20–30 ГБ диска, делай периодическую чистку:
# ===============================

dsp: ##
	docker system prune -af
dvp: ##
	docker volume prune -f
dbp: ##
	docker builder prune -af
dsd: ## посмотреть, что именно занимает место:
	docker system df


# ===============================
# 🔹  востановление базы данных
# ===============================

backup_db: ## создать базу в ручную
	docker-compose exec backup /backups/backup_db.sh

restore_db: ## откатить базу к нужной версии из файла backups
	docker-compose exec backup /backups/restore_db.sh /backups/backup_saasdb_20251009192453.sql.gz
