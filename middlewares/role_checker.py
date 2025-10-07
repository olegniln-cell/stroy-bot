import logging
from typing import Callable, Awaitable, Any, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.user import User
from utils.enums import UserRole

logger = logging.getLogger(__name__)


class RoleCheckerMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        session: AsyncSession = data.get("session")
        if not session:
            raise RuntimeError(
                "DbSessionMiddleware must run before RoleCheckerMiddleware."
            )

        tg_id = None
        if isinstance(event, Message):
            tg_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            tg_id = event.from_user.id

        if tg_id is None:
            return await handler(event, data)

        # ищем по tg_id, а не по id
        result = await session.execute(select(User).where(User.tg_id == tg_id))
        user = result.scalar_one_or_none()

        if not user:
            user = User(
                tg_id=tg_id,
                role=UserRole.worker,  # или UserRole.WORKER.value, если нужно строковое значение
                company_id=None,
            )
            session.add(user)
            await session.flush()
            logger.info("Новый пользователь %s создан.", tg_id)

        data["user"] = user
        return await handler(event, data)
