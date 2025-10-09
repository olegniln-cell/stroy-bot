# Runbook — краткий план действий при инцидентах

## 1) Бот упал (нет polling / ошибки на старте)

* Проверить логи: `docker-compose logs bot --tail 200`
* Если проблема с миграциями: `docker-compose run --rm bot alembic upgrade head`
* Перезапуск: `docker-compose restart bot` или `docker-compose up -d --no-deps --build bot`

## 2) База данных не отвечает

* Проверить контейнер: `docker ps` / `docker-compose ps db`
* Проброс в контейнер: `docker-compose exec db pg_isready -U saasuser -d saasdb`
* Если нужен restore: `gunzip -c backups/backup_X.sql.gz | psql -h db -U saasuser -d saasdb`

## 3) Высокая задержка / рост ошибок

* Посмотреть метрики: Prometheus UI `http://localhost:9090` или `curl http://bot:8080/metrics`
* Посмотреть логи: `docker-compose logs --tail 200`
* Временно отключить воркер/фоновый воркер: `docker-compose stop worker`

## 4) Проверка интеграций error-tracking

* Сгенерировать тестовую ошибку в коде или выполнить: `docker exec -it saasbot python -c "from core.monitoring.hawk_setup import capture_message; capture_message('test')"`
* Проверить панель Hawk/Garage или Sentry.

## 5) Роли и тестовые данные пропали

* Проверить наличие volume postgres: `docker volume ls | grep postgres`
* Если volume был удалён (например `down -v`) — данные потеряны. Восстановление из `backups/`.
* Для тестов использовать test_db с tmpfs (в docker-compose уже сконфигурирован).

## Контакты

* DevOps: @devops
* Backend lead: @backend
