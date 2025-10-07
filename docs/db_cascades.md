Отлично ✅
Вот полный файл **`docs/db_cascades.md`**, который можно сразу вставить в проект:

```markdown
# 🗄️ Каскады и удаление данных

В проекте используется комбинация **CASCADE**, **SET NULL** и **soft delete** (через `deleted_at`).  
Это позволяет гибко управлять связями и безопасно удалять данные.

---

## 📑 Общие правила

1. **Soft delete (`deleted_at`)**
   - используется для сущностей, которые важно хранить (например, `users`, `projects`, `tasks`);
   - запись помечается как удалённая, но не удаляется физически.

2. **CASCADE**
   - если "родительская" запись удаляется — все связанные "дочерние" записи тоже удаляются;
   - используется для зависимостей внутри компании.

3. **SET NULL**
   - при удалении родителя связь обнуляется;
   - данные сохраняются, но без привязки.

---

## 📊 Схема каскадов

| Таблица        | Связь                       | ON DELETE      |
|----------------|-----------------------------|----------------|
| **users**      | → company_id                | CASCADE        |
|                | ← tasks.user_id             | SET NULL       |
|                | ← files.uploader_id         | SET NULL       |
|                | ← sessions.user_id          | CASCADE        |
| **projects**   | → company_id                | CASCADE        |
|                | ← tasks.project_id          | CASCADE        |
| **tasks**      | → company_id                | CASCADE        |
|                | → project_id                | CASCADE        |
|                | → user_id                   | SET NULL       |
|                | ← files.task_id             | CASCADE        |
| **files**      | → company_id                | CASCADE        |
|                | → task_id                   | CASCADE        |
|                | → uploader_id               | SET NULL       |
| **companies**  | ← users.company_id          | CASCADE        |
|                | ← projects.company_id       | CASCADE        |
|                | ← tasks.company_id          | CASCADE        |
|                | ← files.company_id          | CASCADE        |
|                | ← subscriptions.company_id  | CASCADE        |
|                | ← trials.company_id         | CASCADE        |
|                | ← invoices.company_id       | CASCADE        |
| **subscriptions** | → company_id             | CASCADE        |
|                | → plan_id                   | CASCADE        |
| **trials**     | → company_id                | CASCADE        |
| **plans**      | ← subscriptions.plan_id     | CASCADE        |
|                | ← invoices.plan_id          | CASCADE        |
| **invoices**   | → company_id                | CASCADE        |
|                | → plan_id                   | CASCADE        |
|                | ← payments.invoice_id       | CASCADE        |
| **sessions**   | → user_id                   | CASCADE        |
| **payments**   | → invoice_id                | CASCADE        |

---

## 📌 Примеры поведения

- Удаление **Company** → удаляются все `users`, `projects`, `tasks`, `files`, `subscriptions`, `trials`, `invoices`.  
- Удаление **Project** → удаляются связанные `tasks`.  
- Удаление **User** → у задач и файлов `user_id/uploader_id` обнуляется (`SET NULL`).  
- Удаление **Task** → удаляются прикреплённые `files`.  

---

## 📚 Полезные заметки

- **Soft delete** рекомендуется для пользователей и задач — можно восстановить по `deleted_at`.  
- **CASCADE** нужен для "внутренних" связей компании (например, проекты и задачи).  
- **SET NULL** используется там, где данные должны остаться для истории.  

---
