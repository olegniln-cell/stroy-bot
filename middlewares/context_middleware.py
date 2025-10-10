# saas_bot/middlewares/context_middleware.py
import uuid
from typing import Any, Callable, Awaitable, Dict
from core.context import request_id, user_id, company_id
import contextvars

# Новые contextvars
chat_id = contextvars.ContextVar("chat_id", default=None)
username = contextvars.ContextVar("username", default=None)


class ContextMiddleware:
    """
    Middleware для изолированного контекста (request_id, user_id, company_id, chat_id, username)
    при обработке каждого апдейта aiogram.

    - Безопасно для асинхронных тасков
    - Гарантирует сброс контекста
    - Совместимо с aiogram v3
    """

    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: Dict[str, Any],
    ):
        # создаем request_id
        token_req = request_id.set(str(uuid.uuid4()))

        usr = getattr(event, "from_user", None)
        chat = getattr(event, "chat", None)

        # выставляем контекстные переменные
        token_user = user_id.set(getattr(usr, "id", None) if usr else None)
        token_company = company_id.set(None)
        token_chat = chat_id.set(getattr(chat, "id", None) if chat else None)
        token_username = username.set(getattr(usr, "username", None) if usr else None)

        try:
            return await handler(event, data)
        finally:
            # сбрасываем контекст
            request_id.reset(token_req)
            user_id.reset(token_user)
            company_id.reset(token_company)
            chat_id.reset(token_chat)
            username.reset(token_username)
