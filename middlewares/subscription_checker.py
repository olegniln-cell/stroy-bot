import logging
from typing import Callable, Awaitable, Any, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

logger = logging.getLogger(__name__)

# команды/события, которые можно выполнять БЕЗ компании
WHITELIST = (
    "/start",
    "/help",
    "/create_company",
    "/join",
    "/buy",  # можно убрать, если хочешь продавать только членам компании
)


class SubscriptionCheckerMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        has_company: bool = data.get("has_company", False)

        # --- если это callback, всегда пропускаем ---
        if isinstance(event, CallbackQuery):
            return await handler(event, data)

        # --- если это Message ---
        text = (event.text or "").strip()

        # пропускаем whitelisted команды
        if text and any(text.startswith(x) for x in WHITELIST):
            return await handler(event, data)

        # блокируем, если нет компании
        if not has_company:
            await event.answer(
                "Чтобы продолжить, сначала присоединитесь к компании. "
                "Руководитель: /create_company. Рабочий/Бригадир: /join <ID компании>."
            )
            return

        return await handler(event, data)
