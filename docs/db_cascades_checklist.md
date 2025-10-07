# ✅ DB Relations & Cascade Rules

## Soft Delete
- `users.is_active` (bool, default = true)
- `users.deleted_at`
- `projects.deleted_at`
- `tasks.deleted_at`

→ используется для мягкого удаления (данные сохраняются, но помечаются как удалённые).

---

## Каскадные связи
- `projects.company_id → companies.id ON DELETE CASCADE`
- `tasks.project_id → projects.id ON DELETE CASCADE`
- `tasks.user_id → users.id ON DELETE SET NULL`
- `files.task_id → tasks.id ON DELETE CASCADE`
- `files.uploader_id → users.id ON DELETE SET NULL`
- `files.company_id → companies.id ON DELETE CASCADE`
- `trials.company_id → companies.id ON DELETE CASCADE`
- `subscriptions.company_id → companies.id ON DELETE CASCADE`

---

## Проверка каскадов

1. **Удалить юзера**  
   ```sql
   DELETE FROM users WHERE id = X;

   задачи остаются → tasks.user_id = NULL

   файлы остаются → files.uploader_id = NULL

   Удалить проект

   sql
   Копировать код
   DELETE FROM projects WHERE id = X;
   проект исчезает

   все задачи исчезают (CASCADE)

   все файлы этих задач исчезают

   Удалить компанию

   sql
   Копировать код
   DELETE FROM companies WHERE id = X;
   исчезают проекты, задачи, файлы, подписки, триалы

   пользователи исчезают вместе с компанией (в текущей схеме)

   Удалить таску

   sql
   Копировать код
   DELETE FROM tasks WHERE id = X;
   все её файлы исчезают (CASCADE)

   Soft delete

   sql
   Копировать код
   UPDATE tasks SET deleted_at = now() WHERE id = X;
   запись остаётся в БД

   ORM фильтрует (не показывает в списках)

   yaml
   Копировать код

   ---

   👉   2 файла в `docs/`:
   - `db_cascades.sql` → применяемый SQL для фиксации каскадов
   - `db_cascades_checklist.md` → текстовый чек-лист, как проверять руками
