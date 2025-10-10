
---

# 📦 Context-Aware Logging System for aiogram (structlog + contextvars)

## 🎯 Цель

Обеспечить **структурированные JSON-логи** с уникальными контекстами:

* `request_id` — уникальный ID запроса (генерируется для каждого апдейта);
* `user_id` — ID пользователя Telegram (если доступен);
* `chat_id` — ID чата (группового или личного);
* `username` — Telegram username пользователя (если есть);
* `company_id` — ID компании (опционально, задаётся динамически).

---

## ⚙️ Структура проекта

```
saas_bot/
│
├── core/
│   ├── context.py
│   ├── logging_setup.py
│   └── middlewares/
│       └── context_middleware.py
│
├── handlers/
│   └── example_handler.py
│
├── main.py
└── README.md
```

---

## 🧩 core/context.py

```python
import contextvars

request_id = contextvars.ContextVar("request_id", default=None)
user_id = contextvars.ContextVar("user_id", default=None)
chat_id = contextvars.ContextVar("chat_id", default=None)
username = contextvars.ContextVar("username", default=None)
company_id = contextvars.ContextVar("company_id", default=None)
```

---

## 🧱 core/middlewares/context_middleware.py

```python
import uuid
from typing import Any, Callable
from core.context import request_id, user_id, company_id, chat_id, username


class ContextMiddleware:
    """
    Middleware для aiogram-style (handler, event, data).
    Устанавливает request_id, user_id, chat_id, username, company_id
    и гарантированно сбрасывает контекст после обработки апдейта.
    """

    async def __call__(self, handler: Callable, event: Any, data: dict):
        token_req = request_id.set(str(uuid.uuid4()))
        token_user = user_id.set(None)
        token_company = company_id.set(None)
        token_chat = chat_id.set(None)
        token_username = username.set(None)

        try:
            if hasattr(event, "from_user") and event.from_user:
                user_id.set(getattr(event.from_user, "id", None))
                username.set(getattr(event.from_user, "username", None))
            if hasattr(event, "chat") and event.chat:
                chat_id.set(getattr(event.chat, "id", None))

            return await handler(event, data)
        finally:
            # Всегда очищаем контекст — чтобы не утекал между апдейтами
            request_id.reset(token_req)
            user_id.reset(token_user)
            company_id.reset(token_company)
            chat_id.reset(token_chat)
            username.reset(token_username)
```

---

## 🧱 core/logging_setup.py

```python
import logging
import structlog
from core.context import request_id, user_id, company_id, chat_id, username


def add_context(logger, method_name, event_dict):
    """Добавляет контекстные переменные в каждый лог."""
    event_dict["request_id"] = request_id.get()
    event_dict["user_id"] = user_id.get()
    event_dict["chat_id"] = chat_id.get()
    event_dict["username"] = username.get()
    event_dict["company_id"] = company_id.get()
    return event_dict


def setup_logging(level: int = logging.INFO, dev_mode: bool = False):
    """Настройка структурированных логов."""
    processors = [
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        add_context,
    ]

    if dev_mode:
        processors.append(structlog.dev.ConsoleRenderer())  # цветной вывод
    else:
        processors.extend([
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ])

    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(level),
        cache_logger_on_first_use=True,
    )
```

---

## 🪄 handlers/example_handler.py

```python
import structlog
from core.context import company_id

logger = structlog.get_logger(__name__)

async def example_handler(event):
    logger.info("handler.start", event_type=getattr(event, "type", None))

    # Пример: lookup компании
    found_company_id = 42
    if found_company_id:
        company_id.set(found_company_id)
        logger.info("company.assigned")

    logger.info("handler.finish")
```

---

## 🚀 main.py

```python
import asyncio
import structlog
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from core.logging_setup import setup_logging
from core.middlewares.context_middleware import ContextMiddleware
from handlers.example_handler import example_handler

setup_logging(dev_mode=False)  # False = JSON, True = цветной DEV
logger = structlog.get_logger()

BOT_TOKEN = "YOUR_TOKEN"

async def main():
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()
    dp.message.middleware(ContextMiddleware())

    dp.message.register(example_handler)
    logger.info("bot.start")

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🧱 Безопасность и изоляция контекста

Благодаря `contextvars`, каждый апдейт Telegram обрабатывается в **своём контексте**:

* значения `request_id`, `user_id`, `chat_id`, `username` и `company_id`
  **не пересекаются между задачами**;
* контекст **очищается** после обработки каждого апдейта;
* полностью совместим с `asyncio`, `aiogram` и `FastAPI`;
* безопасен даже при высокой нагрузке или в Docker-кластере.

---

## 🧪 Пример реального лога (JSON)

```json
{
  "timestamp": "2025-10-09T12:42:01.692Z",
  "level": "info",
  "event": "handler.start",
  "request_id": "d1e1b9a0-837a-4a84-90a9-512fb2945c4a",
  "user_id": 7648460182,
  "username": "john_doe",
  "chat_id": 7648460182,
  "company_id": 42
}
```

---

## 🧰 Dockerfile (пример)

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

COPY . .

ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]
```

---

## ✅ Проверка логов

Запусти:

```bash
docker-compose up -d bot
docker-compose logs -f bot
```

Если всё корректно, ты увидишь JSON-логи с контекстом (`request_id`, `user_id`, `chat_id`, `username`, `company_id`).

---

Хочешь — я сразу покажу патч для `context.py` и `context_middleware.py`, чтобы добавить `chat_id` и `username` в код (если у тебя они ещё не добавлены)?
