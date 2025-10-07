from aiogram import BaseMiddleware
from typing import Callable, Dict, Any


class DbSessionMiddleware(BaseMiddleware):
    def __init__(self, session_pool):
        super().__init__()
        self.session_pool = session_pool

    async def __call__(self, handler: Callable, event, data: Dict[str, Any]) -> Any:
        async with self.session_pool() as session:
            data["session"] = session  # теперь каждая команда получает сессию
            return await handler(event, data)
