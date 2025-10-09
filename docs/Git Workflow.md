 **профессиональная шпаргалка по Git workflow**,  middle+/senior.

---

## 🚀 Git Workflow — как работают инженеры

### 1. Основные ветки

* **`main`** — стабильная версия, прошедшая все тесты и CI/CD.
  Деплой идёт только с неё.
* **`develop`** *(если используется)* — промежуточная ветка для сборки перед main.
* **Фичи / исправления** — отдельные ветки от main:

  ```
  feat/new-login
  fix/bug-user-session
  chore/ci-improvement
  refactor/db-layer
  test/add-smoke-tests
  ```

---

### 2. Цикл работы с задачей

1️⃣ Создай ветку от main:

```bash
git checkout main
git pull origin main
git checkout -b feat/feature-name
```

2️⃣ Работаешь, коммитишь логично:

```bash
git add .
git commit -m "feat: add user authentication flow"
```

3️⃣ Пушишь ветку:

```bash
git push origin feat/feature-name
```

4️⃣ Открываешь **Pull Request → main**

5️⃣ После успешных CI проверок и ревью:

* Нажимаешь **Merge pull request**
* Потом **удаляешь ветку**:

  ```bash
  git branch -d feat/feature-name
  git push origin --delete feat/feature-name
  ```

---

### 3. Формат коммитов (Conventional Commits)

Используется почти во всех компаниях — удобно для истории и автогенерации changelog.

| Тип         | Назначение                              | Пример                                 |
| ----------- | --------------------------------------- | -------------------------------------- |
| `feat:`     | Новая фича                              | `feat: add user login flow`            |
| `fix:`      | Исправление бага                        | `fix: correct DB migration script`     |
| `chore:`    | Технические правки, CI, формат          | `chore: clean up Docker config`        |
| `refactor:` | Переписывание кода без изменения логики | `refactor: simplify settings loader`   |
| `test:`     | Тесты                                   | `test: add smoke tests for auth`       |
| `docs:`     | Документация                            | `docs: update README with setup steps` |

---

### 4. Работа с CI/CD

* Каждый **PR** должен **запускать GitHub Actions** (тесты, линтеры, сборку).
* PR можно мёржить **только если все проверки зелёные**.
* Никогда не пушим напрямую в `main`.

---

### 5. Короткие команды

| Действие                | Команда                             |
| ----------------------- | ----------------------------------- |
| Обновить main           | `git pull origin main`              |
| Создать ветку           | `git checkout -b feat/xyz`          |
| Добавить всё            | `git add .`                         |
| Коммит                  | `git commit -m "feat: add xyz"`     |
| Пуш                     | `git push origin feat/xyz`          |
| Удалить локальную ветку | `git branch -d feat/xyz`            |
| Удалить удалённую       | `git push origin --delete feat/xyz` |

---

### 6. Бонус — порядок действий при конфликте:

```bash
git pull origin main
# Решаешь конфликты вручную
git add .
git commit
git push
```

---

Хочешь, я сделаю тебе **готовый шаблон git-workflow.md** (файл для репозитория с правилами ветвления, коммитов и CI)?
Он будет как у настоящих компаний — можно положить в `/docs/` и использовать в команде.
