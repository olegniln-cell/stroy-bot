# saas_bot/handlers/example_handler.py
# -*- coding: utf-8 -*-
import structlog
from aiogram import Router, types, F
from aiogram.filters import Command
from core.context import company_id

logger = structlog.get_logger(__name__)

router = Router(name="example")

@router.message(Command("example"))
async def example_handler(message: types.Message):
    logger.info("handler.start", event_type="message")

    # Пример: нашли компанию пользователя
    found_company_id = 42  # пример, будто нашли в БД
    company_id.set(found_company_id)
    logger.info("company.assigned", company_id=found_company_id)

    await message.answer("✅ Пример логирования с контекстом выполнен.")
    logger.info("handler.finish")
