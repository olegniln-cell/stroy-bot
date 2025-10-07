Отлично — разложу всё по полочкам, аккуратно и по-детски понятным языком, и дам **готовый, надёжный и безопасный** SQL-скрипт для проверки «битых» ссылок (fk/orphans), инструкции как и где запускать, что делать с найденным и шаблоны миграций для безопасного устранения проблем.

Коротко — итог: **не удаляем ничего автоматически**. Сначала — проверяем. Если есть оценки >0 — человек смотрит, решает стратегию (NULL / system user / ручная правка / удаление), затем применяем миграцию с backup. Это безопасно и масштабируемо.

---

# 1) Что делает проверочный скрипт и почему он безопасен

* Скрипт **только читает** БД — он НЕ удаляет и НЕ изменяет данные.
* Он динамически проверяет *только те* таблицы/колонки, которые реально есть в вашей базе (чтобы не падать если колонка удалена).
* Для каждой найденной проблемы он показывает:

  * поле (например `files.uploader_id`)
  * количество «висячих» записей (broken\_count)
  * примеры id (до 20) для быстрой ручной проверки

Это позволяет безопасно выявить проблему и принять решение.

---

# 2) Готовый скрипт (безопасный, запускается в psql)

Сохраните как `scripts/check_fk_safe.sql` и запустите (инструкция ниже).

```sql
-- scripts/check_fk_safe.sql
-- Безопасная проверка "висячих" внешних ссылок.
-- Скрипт динамически проверяет только существующие таблицы/колонки и собирает проблемные записи.

DO $$
DECLARE
  checks jsonb := '[
    {"table":"trials","col":"created_by","ref_table":"users","ref_col":"id"},
    {"table":"trials","col":"updated_by","ref_table":"users","ref_col":"id"},

    {"table":"projects","col":"company_id","ref_table":"companies","ref_col":"id"},
    {"table":"projects","col":"created_by","ref_table":"users","ref_col":"id"},
    {"table":"projects","col":"updated_by","ref_table":"users","ref_col":"id"},

    {"table":"tasks","col":"company_id","ref_table":"companies","ref_col":"id"},
    {"table":"tasks","col":"project_id","ref_table":"projects","ref_col":"id"},
    {"table":"tasks","col":"user_id","ref_table":"users","ref_col":"id"},
    {"table":"tasks","col":"created_by","ref_table":"users","ref_col":"id"},
    {"table":"tasks","col":"updated_by","ref_table":"users","ref_col":"id"},
    {"table":"tasks","col":"assignee_id","ref_table":"users","ref_col":"id"},

    {"table":"files","col":"company_id","ref_table":"companies","ref_col":"id"},
    {"table":"files","col":"task_id","ref_table":"tasks","ref_col":"id"},
    {"table":"files","col":"uploader_id","ref_table":"users","ref_col":"id"},
    {"table":"files","col":"project_id","ref_table":"projects","ref_col":"id"},

    {"table":"invoices","col":"company_id","ref_table":"companies","ref_col":"id"},
    {"table":"invoices","col":"plan_id","ref_table":"plans","ref_col":"id"},

    {"table":"payments","col":"invoice_id","ref_table":"invoices","ref_col":"id"},

    {"table":"subscriptions","col":"company_id","ref_table":"companies","ref_col":"id"},
    {"table":"subscriptions","col":"plan_id","ref_table":"plans","ref_col":"id"},

    {"table":"sessions","col":"user_id","ref_table":"users","ref_col":"id"},

    {"table":"users","col":"company_id","ref_table":"companies","ref_col":"id"}
  ]'::jsonb;

  item jsonb;
  sql text;
  cnt bigint;
  sample text;
  first boolean := true;
BEGIN
  RAISE INFO 'Starting FK-orphan check...';

  -- Временная таблица для результатов
  CREATE TEMP TABLE IF NOT EXISTS fk_check_results(
    field text,
    broken_count bigint,
    sample_ids text
  ) ON COMMIT DROP;

  FOR item IN SELECT * FROM jsonb_array_elements(checks)
  LOOP
    -- Проверяем, существует ли таблица и колонка и таблица справочник
    IF EXISTS (
         SELECT 1 FROM information_schema.tables
         WHERE table_schema = 'public' AND table_name = (item->>'table')
       )
       AND EXISTS (
         SELECT 1 FROM information_schema.columns
         WHERE table_schema = 'public' AND table_name = (item->>'table') AND column_name = (item->>'col')
       )
       AND EXISTS (
         SELECT 1 FROM information_schema.tables
         WHERE table_schema = 'public' AND table_name = (item->>'ref_table')
       )
    THEN
      sql := format(
        'SELECT count(*) FROM %I t LEFT JOIN %I r ON t.%I = r.%I WHERE t.%I IS NOT NULL AND r.%I IS NULL',
        item->>'table', item->>'ref_table', item->>'col', item->>'ref_col', item->>'col', item->>'ref_col'
      );
      EXECUTE sql INTO cnt;

      IF cnt > 0 THEN
        sql := format(
          'SELECT string_agg(t.%I::text, '','') FROM (SELECT %I FROM %I t LEFT JOIN %I r ON t.%I = r.%I WHERE t.%I IS NOT NULL AND r.%I IS NULL LIMIT 20) t',
          item->>'col', item->>'col', item->>'table', item->>'ref_table', item->>'col', item->>'ref_col', item->>'col', item->>'ref_col'
        );
        EXECUTE sql INTO sample;

        INSERT INTO fk_check_results VALUES (
          format('%s.%s -> %s', item->>'table', item->>'col', item->>'ref_table'),
          cnt,
          coalesce(sample, '')
        );
      END IF;
    END IF;
  END LOOP;

  -- Вывод результатов (если есть)
  IF (SELECT count(*) FROM fk_check_results) = 0 THEN
    RAISE INFO '✅ No orphan FK references found.';
  ELSE
    RAISE INFO '⚠️ Found orphan FK references. Listing:';
    FOR item IN SELECT * FROM fk_check_results LOOP
      RAISE INFO '% - count=% - sample_ids=%', item.field, item.broken_count, item.sample_ids;
    END LOOP;
    -- Для удобства: также вывести таблицу результатов
    PERFORM (SELECT * FROM fk_check_results);
  END IF;
END;
$$;
```

**Пояснение:** этот блок:

* перебирает список потенциальных проверок (мы перечислили все реальные ссылки, которые есть/могут быть в проекте),
* для каждой проверки гарантирует, что таблицы/колонки существуют,
* считает «битые» ссылки и кладёт их в temp-таблицу,
* печатает результаты (RAISE INFO).
  Ни одна запись не изменяется.

---

# 3) Как и где запускать (простые шаги)

Локально в контейнере Postgres:

```bash
# если используете docker-compose (как у вас)
docker-compose exec db psql -U saasuser -d saasdb -f scripts/check_fk_safe.sql
```

В CI (GitHub Actions) — добавить шаг до миграций/после миграций:

```yaml
- name: Check DB FK orphans
  run: docker-compose exec db psql -U saasuser -d saasdb -f scripts/check_fk_safe.sql
```

(или использовать psql напрямую если сервис postgres в GH Actions).

---

# 4) Что делать если скрипт нашёл проблемы (рекомендация, step-by-step)

1. **Ничего не удаляем автоматически.**

2. **Посмотреть выборку sample\_ids** — понять природу (например: `files.uploader_id` с id 123 -> user с id 123 удалён или миграция убрала FK).

3. **Выбрать стратегию в зависимости от поля:**

   * Для `created_by` / `updated_by` (audit поля) — безопасно ставить `NULL` или назначить `system`/`service` user (например id=1 admin) *после* ручной проверки.
   * Для `files` без `task_id`/`company_id` — внимательно: файл без задачи/компании может быть мусором; лучше пометить на ревью, не удалять мгновенно.
   * Для `payments` без `invoice` — это критично (финансовые записи) — разбирательство вручную.

4. **Примеры безопасных исправлений (вручную, с бэкапом!):**

   * поставить NULL:

     ```sql
     UPDATE files
     SET uploader_id = NULL
     WHERE uploader_id IS NOT NULL
       AND NOT EXISTS (SELECT 1 FROM users u WHERE u.id = files.uploader_id);
     ```
   * назначить system user (если вы заранее создали id=1 admin):

     ```sql
     UPDATE files
     SET uploader_id = 1
     WHERE uploader_id IS NOT NULL
       AND NOT EXISTS (SELECT 1 FROM users u WHERE u.id = files.uploader_id);
     ```

5. **После исправления** — если вы хотите вернуть целостность FK:

   * подготовить миграцию, где вы:

     1. фиксируете/исправляете данные (UPDATE ... SET NULL/1 ...),
     2. добавляете/пересоздаёте FK с `ON DELETE SET NULL` для ссылок на users (safe),
     3. используете `ON DELETE CASCADE` для company → project/subscriptions/invoices если это бизнес-логика (или лучше — soft delete).
   * пример Alembic upgrade snippet (фрагмент):

     ```py
     def upgrade():
         # очистка "битых" записей
         op.execute("""
           UPDATE files
           SET uploader_id = NULL
           WHERE uploader_id IS NOT NULL
             AND NOT EXISTS (SELECT 1 FROM users WHERE users.id = files.uploader_id)
         """)

         # смена FK: сначала drop, потом create с ON DELETE SET NULL
         op.drop_constraint(op.f('files_uploader_id_fkey'), 'files', type_='foreignkey')
         op.create_foreign_key('files_uploader_id_fkey', 'files', 'users', ['uploader_id'], ['id'], ondelete='SET NULL')
     ```

6. **Всегда** делаем backup перед массовыми обновлениями. На чистой (CI) базе — можно тестировать заранее.

---

# 5) Соответствие вашему проекту (проверка на соответствие структуры)

Я включил в проверочный список все типичные пары, которые вы использовали в моделях и миграциях (и которые вы показывали в логах): `users`, `companies`, `projects`, `tasks`, `files`, `invoices`, `payments`, `plans`, `subscriptions`, `sessions`, `trials`.
Скрипт **проверяет только существующие таблицы/колонки**, поэтому он безопасно пропустит то, чего у вас нет (и не упадёт).

Если вы хотите — я могу подправить список проверок (в JSON в начале DO-блока), чтобы он строго соответствовал текущему коду из вашего гиста — но это не обязательно: текущий список охватывает всё нужное и пропустит отсутствующие поля.

---

# 6) Стратегические рекомендации (фундаментально, масштабируемо)

* **Не удалять данные автоматически.** Всегда сначала report → review → fix → recheck.
* Для `users` лучше `ON DELETE SET NULL` или soft-delete (is\_deleted + status). Это сохраняет историю.
* Для `company` можно использовать CASCADE логично (company удалена → проекты, подписки удалены). Но я рекомендую мягкое удаление компании (is\_deleted), чтобы избежать неожиданного удаления большого объёма данных.
* Включите этот FK-check в CI: **каждый PR**/каждый deploy запускает скрипт. Если появляются орфаны — CI fail или report в Slack.
* Добавьте `check_fk_safe.sql` как cron/health check в staging/production мониторинг: так вы будете видеть «дрейф» в целостности.

---

# 7) Что делать прямо сейчас (пошагово)

1. Сохраните `scripts/check_fk_safe.sql` в репо.
2. Запустите локально в dev:
   `docker-compose exec db psql -U saasuser -d saasdb -f scripts/check_fk_safe.sql`
3. Разберите вывод: если пусто — отлично. Если нет — сохраните sample\_ids и исследуйте 1–3 проблемы вручную.
4. Для каждого типа проблемы выберите стратегию (NULL / system user / manual clean / report to product).
5. Подготовьте Alembic-миграцию с safe-fix (UPDATE ...), протестируйте на чистой БД (CI job).
6. После успешной фиксации и тестов — примените в staging/production с бэкапом.

---

# 8) Короткие ответы на ваши вопросы «нужно ли сейчас удалять ссылки?» и т.п.

* **Нужно ли удалять прямо сейчас?** — нет. Сначала нужно проверить, понять причину и принять решение. Авто-удаление — рискованно.
* **Как этот скрипт помогает стратегически?** — это профилактика: выявляет нарушения целостности до того, как вы захотите навязать новые FK или применять другие миграции; помогает держать DB «здоровой».
* **Можно ли включить в CI?** — да, обязательно. CI должен либо fail, либо report (в зависимости от политики) при обнаружении орфанов.
* **Опасно ли запускать в prod?** — нет, скрипт только читает. Но **исправительные SQL** (UPDATE/DELETE) — делать только после бэкапа и ревью.

---

Если хочешь, сделаю ещё:

* адаптацию списка проверок строго под твои текущие модели из гиста (проверю имена колонок и уберу ненужное);
* дам готовый Alembic миграционный шаблон для **безопасного** применения fix (UPDATE + FK recreate ON DELETE SET NULL/CASCADE с описанием);
* добавлю шаг в твой GitHub Actions workflow, который запускает `psql -f scripts/check_fk_safe.sql` и — если есть результаты — печатает их и, при желании, фейлит job.

Что сделать дальше?
Скажи одно из:

1. «Прогоняй» — и я дам команду/шаги, чтобы ты сам запустил этот скрипт сейчас и прислал вывод.
2. «Сделай миграцию-шаблон» — и я сгенерирую Alembic-шаблон, который безопасно исправляет `files.uploader_id`, `tasks.user_id` и создаёт FK с `ON DELETE SET NULL`.
3. «Адаптируй скрипт под гист» — я подгоню список проверок строго под текущие модели в твоём гисте.

Выбирай — сделаю прямо сейчас.
