# middlewares/audit_middleware.py

from aiogram import BaseMiddleware
from typing import Callable, Dict, Any


class AuditMiddleware(BaseMiddleware):
    async def __call__(
        self, handler: Callable, event: Any, data: Dict[str, Any]
    ) -> Any:
        session = data.get("session")
        user = data.get("event_from_user")  # aiogram user

        if session and user:
            session.info["actor_id"] = user.id  # сохраняем Telegram ID для связи

        return await handler(event, data)
