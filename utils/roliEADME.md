

ЗАПРОС
сейчас в базе так user_role | user user_role | admin user_role | manager в коде так WORKER = "worker" # рабочий FOREMAN = "foreman" # бригадир MANAGER = "manager" # руководитель ADMIN = "admin" # администратор задача в базе user_role | user думаю что. не нужен!!! Ты что думаешь? а нужен - WORKER = "worker" # рабочий FOREMAN = "foreman" # бригадир как это пересобрать ?если это нельяза пересобрать с уже существующими миграциями может тогда удалит все внести в тумиграуию где это должно быть что бы структура эта была правильная? вот все миграции которые применились которые прогоняются без ошибок https://gist.github.com/FinoSag/42b6daa0dd8f7c71d4ed5b1503f9d7ab открылись? как быть в такой ситуации предложи оптимальынй лучши вариант который будет надежным в будующем что бы небыло ошибок и в будующем не пришлось переделывать глобально не понимаю почему туа сложно удалять не нужные роли или добавлять И Сравни с код проанализируй детально как сейчас устроены роли дай отчет как устроено ? какие роли сейчас в коде? какая логика? в хендлерах? в моделях? и других файлах? https://gist.github.com/FinoSag/ef17d38898e6bd734c6ffac84e1b5365 открылся файл? Можно ли переходить к следущей задачи? 5. CI: добавить job migrations_apply_on_clean_db: ◦ поднимать чистый Postgres (в CI job), ◦ alembic upgrade head, ◦ запуск check_models_vs_db.py, ◦ запуск smoke-integration tests (create company → trial). ◦ Если alembic revision --autogenerate даёт diff — падать CI. 6. Acceptance criteria (фаза 1): alembic upgrade head на чистой БД проходит без ошибок; все smoke tests проходят. Не решив задачу с ролями или нужно сначала решить вопрос с ролями что бы было все понятно


Ты правильно уловил ключевую проблему — у вас сейчас **рассинхрон между кодом и БД по ролям**, и если это не решить, то CI, миграции и проверки будут постоянно ломаться.

📊 **Разбор ситуации:**

* **В БД (`user_role`)**: `user`, `admin`, `manager`.
* **В коде (`UserRole`)**: `worker`, `foreman`, `manager`, `admin`.
* **Несовпадение:** в коде нет `user`, а в БД нет `worker` и `foreman`.
* **Логика в коде:** хендлеры и middleware реально ждут `WORKER`, `FOREMAN`, `MANAGER`, `ADMIN`.

👉 Это значит, что текущий `enum` в базе *не соответствует бизнес-логике кода*.
Если ты сейчас "подгонишь код под БД" (т.е. добавишь `USER` обратно и выкинешь `WORKER/FOREMAN`), то:

* миграции будут чистыми,
* CI будет проходить,
* **но логика ролей в коде сломается**, потому что проверки доступа (`if user.role == UserRole.WORKER`) перестанут работать.

---

### 🔑 Оптимальный и надежный вариант (рекомендую):

1. **Не менять код под базу**, а наоборот — привести базу к коду.
   То есть оставить четыре роли:

   * `worker`
   * `foreman`
   * `manager`
   * `admin`
     и убрать старую `user`.

2. **Сделать миграцию на замену enum (через новый тип)**:

   * Создать новый `enum` со всеми актуальными ролями.
   * Добавить временную колонку.
   * Перемапить данные (`user → worker`).
   * Дропнуть старый enum и заменить новым.

3. **В будущем** — держать тест, который проверяет, что роли в коде и в базе совпадают.

---

### 📌 Почему нельзя просто удалить `user` из enum?

* PostgreSQL не позволяет дропнуть значение из enum, если оно используется.
* Даже если не используется — прямого `ALTER TYPE DROP VALUE` тоже нет (только через "новый тип").

---

### ⚙️ Как быть с текущими миграциями?

* Судя по gist, у тебя цепочка уже применяется.
* Лучше **создать новую миграцию поверх**, а не переписывать старые (иначе сломается история миграций у всех разработчиков).
* В новой миграции аккуратно сделать замену ролей как я описал выше.

---

### 🚦 План действий (коротко):

1. Создать миграцию `xxxx_update_user_role_enum.py`.
2. В ней:

   * создать `user_role_new (worker, foreman, manager, admin)`
   * добавить колонку `role_new`
   * перемапить данные (`user → worker`, остальные оставить)
   * удалить старую колонку, старый тип
   * переименовать колонку и новый enum в старые имена.
3. Прогнать `alembic upgrade head` на чистой базе.
4. Прогнать `check_models_vs_db.py`.
5. Убедиться, что `alembic revision --autogenerate` не даёт diff.
6. Добавить тест, сверяющий роли из БД и из Python enum.

---

🔥 Таким образом:

* ты не теряешь данные,
* код и база синхронизированы,
* в будущем CI гарантирует, что роли не разъедутся.

---

Хочешь, я прямо подготовлю тебе готовую Alembic-миграцию (код upgrade/downgrade), которую ты можешь вставить и проверить?




ВНЕСЕННЫЕ ИЗМЕНЕНИЯ
Ниже — аккуратная **«бокс-инструкция»** (шаг-за-шаг) с готовым кодом миграции, командами и тестом. Она безопасно переводит Postgres `user_role (user, admin, manager)` → набор ролей в коде `worker, foreman, manager, admin`, не ломая данных, и оставляет историю миграций чистой.

> ⚠️ Перед началом — обязательно сделай бэкап БД и протестируй миграцию на копии (restore/test). Команды для бэкапа есть внизу.

---

# 1) Краткая логика действий

1. Создать новый enum `user_role_new` с нужными значениями (`worker`, `foreman`, `manager`, `admin`).
2. Добавить в таблицу `users` временную колонку `role_new` с типом `user_role_new`.
3. Скопировать (перемапить) данные: `user -> worker`, остальные — соответствующим образом.
4. Удалить старую колонку `role`.
5. Поменять имена типов/колонок: `user_role_new` → `user_role`, `role_new` → `role`.
6. Прогнать `alembic upgrade head`, проверить всё (enum в БД, check\_models, autogen, smoke tests).
7. Добавить тест, проверяющий синхронизацию enum в коде и БД.

---

# 2) Alembic-миграция — полное содержимое файла

Создай файл, например `migrations/versions/20250913_update_user_role_enum.py` (назови по своему стандарту). Вставь этот код, **замени** `down_revision` на текущую ревизию (`34b46aedc031` у тебя) и проставь `revision` уникально (uuid/токен).

```python
# migrations/versions/20250913_update_user_role_enum.py
"""Replace user_role enum: add worker, foreman; map 'user' -> 'worker' safely.

Revision ID: 20250913_update_user_role_enum
Revises: 34b46aedc031
Create Date: 2025-09-13
"""
from alembic import op
import sqlalchemy as sa

revision = "20250913_update_user_role_enum"
down_revision = "34b46aedc031"
branch_labels = None
depends_on = None

def upgrade():
    # 1) Create new enum type
    op.execute("CREATE TYPE user_role_new AS ENUM ('worker','foreman','manager','admin')")

    # 2) Add new nullable column using the new enum
    op.add_column(
        "users",
        sa.Column(
            "role_new",
            sa.Enum("worker","foreman","manager","admin", name="user_role_new"),
            nullable=True
        )
    )

    # 3) Map/transfer existing values: user -> worker; keep admin/manager as-is
    op.execute("""
        UPDATE users
        SET role_new = CASE role::text
            WHEN 'user' THEN 'worker'
            WHEN 'admin' THEN 'admin'
            WHEN 'manager' THEN 'manager'
            ELSE 'worker'
        END::user_role_new
    """)

    # 4) (Optional) ensure values populated (you may add checks/logging here)
    # 5) Drop old column 'role'
    op.drop_column('users', 'role')

    # 6) Remove old type and rename new type to original name
    op.execute("DROP TYPE IF EXISTS user_role")
    op.execute("ALTER TYPE user_role_new RENAME TO user_role")

    # 7) Rename column role_new -> role
    op.alter_column('users', 'role_new', new_column_name='role')

    # 8) (Optional) set NOT NULL if desired:
    # op.alter_column('users', 'role', nullable=False)


def downgrade():
    # Reverse: create old type and map back worker/foreman -> user
    op.execute("CREATE TYPE user_role_old AS ENUM ('user','admin','manager')")

    op.add_column(
        'users',
        sa.Column(
            'role_old',
            sa.Enum('user','admin','manager', name='user_role_old'),
            nullable=True
        )
    )

    op.execute("""
        UPDATE users
        SET role_old = CASE role::text
            WHEN 'worker' THEN 'user'
            WHEN 'foreman' THEN 'user'
            WHEN 'admin' THEN 'admin'
            WHEN 'manager' THEN 'manager'
            ELSE 'user'
        END::user_role_old
    """)

    op.drop_column('users', 'role')

    # drop current type and restore name
    op.execute("DROP TYPE IF EXISTS user_role")
    op.execute("ALTER TYPE user_role_old RENAME TO user_role")

    op.alter_column('users', 'role_old', new_column_name='role')
```

**Пояснения:**

* Мы создаём новый тип `user_role_new`, добавляем `role_new`.
* Копируем данные через `role::text` → new enum (приведение).
* Удаляем старую колонку и старый тип, затем переименовываем `user_role_new` -> `user_role`.
* `downgrade()` возвращает обратно (маппирует `worker/foreman` → `user`) — это базовый rollback.

---

# 3) Команды — пошагово (локально через Docker Compose)

Перед началом — сделай бэкап:

```bash
# создаём каталог для бэкапов (на хосте)
mkdir -p ./backups

# дамп БД в файл на хосте (может потребовать -T для корректного перенаправления)
docker-compose exec -T db pg_dump -U saasuser saasdb > ./backups/saasdb_before_enum.sql
```

Потом выполняем миграцию (предполагается, что в контейнере `bot` есть alembic и настроен DATABASE\_URL):

```bash
# 1. Добавить файл миграции (в git), затем:
git add migrations/versions/20250913_update_user_role_enum.py
git commit -m "Add migration: update user_role enum (add worker, foreman)"

# 2. На копии/локальной dev БД запусти миграцию:
docker-compose exec bot alembic upgrade head
```

Проверки после применения:

```bash
# покажем текущую ревизию
docker-compose exec bot alembic current

# покажем значения enum
docker-compose exec db psql -U saasuser -d saasdb -c "SELECT e.enumlabel FROM pg_type t JOIN pg_enum e ON t.oid=e.enumtypid WHERE t.typname='user_role' ORDER BY e.enumsortorder;"

# проверь сколько пользователей в каждой роли
docker-compose exec db psql -U saasuser -d saasdb -c "SELECT role, count(*) FROM users GROUP BY role;"

# прогоняем проверку моделей
docker-compose exec bot python scripts/check_models_vs_db.py

# проверка alembic autogenerate (autogen check)
docker-compose exec bot alembic revision --autogenerate -m "autogen_check" || true
# если создался файл migrations/versions/*autogen_check*.py — CI должен падать; удалите созданный файл после проверки:
docker-compose exec bot bash -lc "ls -1 migrations/versions | grep autogen_check || true"
# (если файл появится) удалить его:
docker-compose exec bot bash -lc "rm -f migrations/versions/*autogen_check*.py || true"
```

---

# 4) Тест, который гарантирует синхронизацию enum в коде и БД

Создай тест `tests/test_enum_sync.py`:

```python
# tests/test_enum_sync.py
import os
from sqlalchemy import create_engine, text
import pytest

# Импортируй свой UserRole точно оттуда, где он живёт в проекте
# Пример:
try:
    from app.utils.enums import UserRole
except Exception:
    from utils.enums import UserRole

@pytest.mark.smoke
def test_user_role_enum_sync():
    db_url = os.environ.get("DATABASE_URL", "postgresql://saasuser:saaspass@db:5432/saasdb")
    # strip async driver suffix if present
    db_sync = db_url.replace("+asyncpg", "").replace("asyncpg+", "")
    engine = create_engine(db_sync)
    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT e.enumlabel FROM pg_type t JOIN pg_enum e ON t.oid = e.enumtypid "
            "WHERE t.typname = 'user_role' ORDER BY e.enumsortorder"
        )).fetchall()
        db_roles = [r[0] for r in rows]
    code_roles = [r.value for r in UserRole]
    assert set(db_roles) == set(code_roles), f"DB roles {db_roles} != code roles {code_roles}"
```

Запуск теста локально:

```bash
docker-compose exec bot pytest -q tests/test_enum_sync.py
```

Добавь этот тест в набор smoke-tests, чтобы CI гарантировал соответствие.

---

# 5) Полная проверочная последовательность (резюме команд)

1. Сделать бэкап:

```bash
docker-compose exec -T db pg_dump -U saasuser saasdb > ./backups/saasdb_before_enum.sql
```

2. Создать миграцию файл (см. выше), закоммитить.

3. Прогнать миграцию:

```bash
docker-compose exec bot alembic upgrade head
```

4. Проверить значения enum:

```bash
docker-compose exec db psql -U saasuser -d saasdb -c "SELECT enumlabel FROM pg_type t JOIN pg_enum e ON t.oid=e.enumtypid WHERE t.typname='user_role' ORDER BY e.enumsortorder;"
```

5. Проверить, что данные переведены:

```bash
docker-compose exec db psql -U saasuser -d saasdb -c "SELECT role, COUNT(*) FROM users GROUP BY role;"
```

6. Проверить модели:

```bash
docker-compose exec bot python scripts/check_models_vs_db.py
```

7. Проверка автогенерации (CI-проверка):

```bash
docker-compose exec bot alembic revision --autogenerate -m "autogen_check" || true
# Убедиться, что не появился файл autogen_check.py в migrations/versions
```

8. Прогнать smoke-tests (включая тест синхронизации enum):

```bash
docker-compose exec bot pytest -q -m smoke
```

Если все зелёное — можно включать job `migrations_apply_on_clean_db` в CI.

---

# 6) Замечания, риски и предосторожности

* **Бэкап обязателен**. Создай дамп и/или snapshot volume перед применением в staging/production.
* **Проверь, нет ли других колонок/таблиц, использующих `user_role`**. Выполни:

  ```sql
  SELECT n.nspname, c.relname, a.attname
  FROM pg_catalog.pg_attribute a
  JOIN pg_class c ON a.attrelid = c.oid
  JOIN pg_type t ON a.atttypid = t.oid
  JOIN pg_namespace n ON c.relnamespace = n.oid
  WHERE t.typname = 'user_role' AND a.attnum > 0;
  ```

  — если другие колонки есть, их тоже нужно обработать (аналогично `role_new` добавлять для каждой).
* **Downtime**: операция не требует долгого даунтайма, но лучше проводить в maintenance window для продакшена.
* **Если у вас foreign keys / triggers / default values ссылаются на этот enum —** заранее проверь и скорректируй миграцию.
* **Порядок миграций**: не переписывай старые миграции — создавай новую сверху (history preserved).

---

# 7) Обнови код (если ещё не обновлён)

Убедись, что `UserRole` в коде совпадает:

```python
# app/utils/enums.py
from enum import Enum

class UserRole(str, Enum):
    WORKER = "worker"
    FOREMAN = "foreman"
    MANAGER = "manager"
    ADMIN = "admin"
```

Коммитни это изменение. После миграции и этого коммита у тебя будет консистентность: код ↔ БД.

---

# 8) Готовность к CI (ответ на твой вопрос)

После выполнения вышеописанных шагов и успешного прохождения:

* `alembic upgrade head` на чистой БД,
* `check_models_vs_db.py` без несогласованностей (игнорируя alembic\_version),
* `alembic revision --autogenerate` — не даёт diff,
* smoke-tests (включая тест enum\_sync) зелёные —
  тогда **можно включать CI job migrations\_apply\_on\_clean\_db**.

---

Если хочешь, могу:

* 1. сгенерировать для тебя готовый файл миграции с конкретным `revision` (и сразу вставить `down_revision` равным твоему head),
* 2. подготовить готовый smoke-test, пометить его `@pytest.mark.smoke` (я уже привёл пример),
* 3. дать команды для восстановления из бэкапа (если что-то пойдёт не так).

Скажи — сгенерировать и вставить миграцию прямо сейчас?
