import asyncio
import logging
import os

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from database import init_db, async_session_maker
from services import notify_jobs

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("worker")

BOT_TOKEN = os.getenv("BOT_TOKEN")


async def run_jobs():
    """Оберточная функция для запуска задач"""
    async with async_session_maker() as session:
        bot = Bot(BOT_TOKEN)
        await notify_jobs.run_all(session, bot)
        await bot.session.close()
    logger.info("✅ Все задачи выполнены")


async def main():
    logger.info("🚀 Worker started")
    await init_db()

    scheduler = AsyncIOScheduler(timezone="UTC")

    # Запускаем каждый день в 09:00 UTC
    scheduler.add_job(run_jobs, CronTrigger(hour=9, minute=0))

    # Дополнительно первый запуск сразу при старте контейнера
    asyncio.create_task(run_jobs())

    scheduler.start()

    # Вечный цикл
    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())
