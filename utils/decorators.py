# utils/decorators.py
from functools import wraps
from aiogram.types import Message, CallbackQuery
from services.subscriptions import get_company_subscription_status

from utils.enums import UserRole


def is_manager(func):
    @wraps(func)
    async def wrapper(event: Message | CallbackQuery, *args, **kwargs):
        user = kwargs.get("user")
        if not user or user.role != UserRole.manager:
            await (
                event.answer if isinstance(event, Message) else event.message.answer
            )("У вас нет прав для выполнения этой команды.")
            return
        return await func(event, *args, **kwargs)

    return wrapper


def is_manager_or_foreman(func):
    @wraps(func)
    async def wrapper(event: Message | CallbackQuery, *args, **kwargs):
        user = kwargs.get("user")
        if not user or user.role not in (UserRole.manager, UserRole.foreman):
            await (
                event.answer if isinstance(event, Message) else event.message.answer
            )("У вас нет прав для выполнения этой команды.")
            return
        return await func(event, *args, **kwargs)

    return wrapper


def require_active_subscription():
    def decorator(func):
        @wraps(func)
        async def wrapper(event: Message | CallbackQuery, *args, **kwargs):
            # aiogram v3: зависимости приходят напрямую в kwargs
            session = kwargs.get("session")
            user = kwargs.get("user")

            if not user or not getattr(user, "company_id", None):
                if isinstance(event, Message):
                    await event.answer("⛔ Сначала присоединитесь к компании.")
                else:
                    await event.answer(
                        "⛔ Сначала присоединитесь к компании.", show_alert=True
                    )
                return

            st = await get_company_subscription_status(session, user.company_id)
            if not st["available"]:
                if isinstance(event, Message):
                    await event.answer("⛔ Нет активной подписки.")
                else:
                    await event.answer("⛔ Нет активной подписки.", show_alert=True)
                return

            return await func(event, *args, **kwargs)

        return wrapper

    return decorator
