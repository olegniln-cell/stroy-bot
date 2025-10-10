# saas_bot/handlers/example_handler.py
# -*- coding: utf-8 -*-
import structlog
import time  # ✅ добавь
from aiogram import Router, types
from aiogram.filters import Command
from core.context import company_id
from prometheus_client import Counter, Histogram  # ✅ добавь

logger = structlog.get_logger(__name__)

router = Router(name="example")

# --- Метрики (используем те же имена, что и в main.py) ---
BOT_REQUESTS = Counter("bot_requests_total", "Total bot requests handled")
BOT_LATENCY = Histogram("bot_latency_seconds", "Bot handler latency")


@router.message(Command("example"))
async def example_handler(message: types.Message):
    start_time = time.time()  # ✅ начинаем измерять время
    BOT_REQUESTS.inc()  # ✅ увеличиваем счётчик запросов

    try:
        logger.info("handler.start", event_type="message")

        # Пример: нашли компанию пользователя
        found_company_id = 42  # пример, будто нашли в БД
        company_id.set(found_company_id)
        logger.info("company.assigned", company_id=found_company_id)

        # 💥 Искусственно выбрасываем исключение, чтобы проверить Hawk
        raise ValueError("🧨 Hawk real exception test")

        await message.answer("✅ Пример логирования с контекстом выполнен.")
        logger.info("handler.finish")

    finally:
        # ✅ записываем время выполнения
        BOT_LATENCY.observe(time.time() - start_time)
