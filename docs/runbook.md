
### 4. 📘 Runbook (операционный гайд)

````md
# 🧭 Runbook — эксплуатация бота

## Проверка статуса
```bash
make ps       # список контейнеров
curl localhost:8080/healthz
````

## Метрики

```
curl localhost:8080/metrics
```

## Бэкап БД

```
docker exec saasbot_backup /backups/backup_db.sh
```

## Просмотр логов

```
make logs
```

## Перезапуск бота

```
make down && make up
```

```
