3️⃣ Полная последовательность команд для запуска локально

поднимает чистый Postgres,
применяет миграции,
запускает check_models_vs_db.py,
запускает этот smoke_tests.py,
падает CI, если есть diff в миграциях.


Чтобы проверить, что всё работает и CI тоже сработает:

# 1. Поднять контейнеры
docker-compose up -d db bot

# 2. Применить миграции
docker-compose exec bot alembic upgrade head

# 3. Применить seed
docker-compose exec bot python -m scripts.seed

# 4. Проверить модели vs БД
docker-compose exec bot python scripts/check_models_vs_db.py

# 5. Запустить smoke-тесты локально
docker-compose exec bot pytest tests/integration/smoke_tests.py

# 6. Проверить FK и индексы (опционально)
docker-compose exec db psql -U saasuser -d saasdb -c "\d"


После этого можно заливать workflow в GitHub, пушить ветку, и CI должен:

Поднять чистый Postgres
Применить alembic upgrade head
Проверить модели через check_models_vs_db.py
Прогнать smoke-тесты
Проверить, что alembic revision --autogenerate не выдаёт diff

✅ Если всё прошло — фаза 1 закрыта, можно переходить к фазе 2 (наблюдаемость и бэкапы).
