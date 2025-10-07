# middlewares/company_middleware.py
import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from models import User

logger = logging.getLogger(__name__)


class CompanyMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        user: User = data.get("user")
        session: AsyncSession = data.get("session")
        if not user:
            raise RuntimeError(
                "CompanyMiddleware must run after RoleCheckerMiddleware."
            )
        if not session:
            raise RuntimeError("DbSessionMiddleware must run before CompanyMiddleware.")

        data["has_company"] = user.company_id is not None
        logger.info(
            "CompanyMiddleware: tg_id=%s has_company=%s company_id=%s",
            user.tg_id,
            data["has_company"],
            user.company_id,
        )

        cid = user.company_id if user.company_id is not None else -1
        # имя настройки синхронизировано: app.company_id
        await session.execute(text(f"SET LOCAL app.company_id = {cid}"))

        return await handler(event, data)
