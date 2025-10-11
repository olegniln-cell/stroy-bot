# -*- coding: utf-8 -*-
import os
import asyncio
import structlog
from aiogram import Bot, Dispatcher
from middlewares.context_middleware import ContextMiddleware
from prometheus_client import CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST

from core.logging_setup import setup_logging
from config import BOT_TOKEN, NOTIFY_CHECK_INTERVAL_MIN, DATABASE_URL
from database import init_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio.session import async_sessionmaker
from aiohttp import web
from urllib.parse import urlparse

# routers
from handlers.start import router as start_router
from handlers.help import router as help_router
from handlers.company import router as company_router
from handlers.invite import router as invite_router
from handlers.projects import router as projects_router
from handlers.tasks import router as tasks_router
from handlers.reassign import router as reassign_router
from handlers.status import router as status_router
from handlers.reports import router as reports_router
from handlers.user import router as user_router
from handlers.file_upload import router as file_upload_router
from handlers.files import router as files_router
from handlers.important_stuff import router as important_router
from handlers import admin_billing
from handlers import admin
from handlers import payments
from handlers import example_handler

# middlewares
from middlewares.db_middleware import DbSessionMiddleware
from middlewares.role_checker import RoleCheckerMiddleware
from middlewares.company_middleware import CompanyMiddleware
from middlewares.subscription_checker import SubscriptionCheckerMiddleware
from middlewares.audit_middleware import AuditMiddleware
from middlewares.metrics_middleware import MetricsMiddleware, init_metrics

# jobs
from services.notify_jobs import (
    notify_expiring_trials,
    notify_expiring_subscriptions,
    enforce_expirations,
)
from services.seed import seed_plans

# --- Hawk integration ---
from core.monitoring.hawk_setup import setup_hawk, capture_exception, capture_message

# --- фоновые напоминания просроченных задач  ---
from services.notifications.scheduler import start_scheduler


# --- Structlog logging setup ---
setup_logging()
logger = structlog.get_logger(__name__)

# создаём отдельный реестр, чтобы избежать дубликатов
registry = CollectorRegistry()

# инициализируем метрики
init_metrics(registry)

# Инициализация Hawk при старте
setup_hawk()


# --- Глобальный перехватчик необработанных ошибок ---
def handle_uncaught_exception(loop, context):
    msg = context.get("exception") or context.get("message")
    logger.error(f"🔥 Uncaught exception: {msg}")

    try:
        if context.get("exception"):
            capture_exception(context.get("exception"))
        else:
            capture_message(str(msg))
    except Exception as e:
        logger.warning(f"⚠️ Failed to report error to Hawk: {e}")


# --- Health-check server ---
async def start_health_server():
    async def handle_health(request):
        return web.Response(text="OK", status=200)

    async def handle_metrics(request):
        try:
            data = generate_latest(registry)
            # aiohttp >= 3.9 не принимает charset в content_type
            safe_content_type = CONTENT_TYPE_LATEST.split(";")[0]
            return web.Response(body=data, content_type=safe_content_type)
        except Exception as e:
            logger.exception("metrics endpoint error", error=str(e))
            return web.Response(status=500, text=f"metrics error: {e}")

    app = web.Application()
    app.router.add_get("/healthz", handle_health)
    app.router.add_get("/metrics", handle_metrics)

    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    logger.info(f"🩺 Health-check + Metrics запущены на порту {port}")
    logger.info("🟢 Bot ready: healthz OK, metrics OK, polling starting…")


async def main():
    # --- Log env info (safe) ---
    db_host = urlparse(DATABASE_URL).hostname
    logger.info("[BOOT] Запуск бота")
    logger.info("[BOOT] DB host", db_host=db_host)
    logger.info("[BOOT] BOT_TOKEN (prefix only)", prefix=BOT_TOKEN[:6])

    logger.info("[INFO] Инициализация базы данных...")
    session_pool: async_sessionmaker[AsyncSession] = await init_db()
    logger.info("[INFO] База данных готова")

    # безопасный сид тарифов (один раз при старте)
    async with session_pool() as s:
        await seed_plans(s)
        await s.commit()

    # --- Health-check ---
    asyncio.create_task(start_health_server())

    # --- Telegram Bot ---
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # порядок middleware критичен
    dp.message.middleware(DbSessionMiddleware(session_pool))
    dp.callback_query.middleware(DbSessionMiddleware(session_pool))

    dp.message.middleware(RoleCheckerMiddleware())
    dp.callback_query.middleware(RoleCheckerMiddleware())

    dp.message.middleware(CompanyMiddleware())
    dp.callback_query.middleware(CompanyMiddleware())

    dp.message.middleware(SubscriptionCheckerMiddleware())
    dp.callback_query.middleware(SubscriptionCheckerMiddleware())

    dp.message.middleware(AuditMiddleware())
    dp.callback_query.middleware(AuditMiddleware())

    dp.update.middleware(ContextMiddleware())

    dp.message.middleware(MetricsMiddleware())
    dp.callback_query.middleware(MetricsMiddleware())

    # routers
    dp.include_router(start_router)
    dp.include_router(help_router)
    dp.include_router(company_router)
    dp.include_router(invite_router)
    dp.include_router(projects_router)
    dp.include_router(tasks_router)
    dp.include_router(reassign_router)
    dp.include_router(status_router)
    dp.include_router(reports_router)
    dp.include_router(user_router)
    dp.include_router(file_upload_router)
    dp.include_router(files_router)
    dp.include_router(important_router)
    dp.include_router(admin_billing.router)
    dp.include_router(payments.router)
    dp.include_router(admin.router)

    # Пример логирования (тестовый хэндлер)
    dp.include_router(example_handler.router)

    # фоновый воркер
    asyncio.create_task(billing_notifier(bot, session_pool))

    # --- Планировщик дедлайнов задач ---

    start_scheduler(bot, session_pool)

    logger.info("[INFO] Бот запускается...")

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        logger.info("🧩 Shutting down gracefully...")
        # отменяем все фоновые задачи
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        for t in tasks:
            t.cancel()

        # закрываем сессию Telegram-бота
        await bot.session.close()

        # даём немного времени задачам завершиться
        await asyncio.sleep(0.1)

        logger.info("[INFO] Бот остановлен.")


async def billing_notifier(bot: Bot, session_pool: async_sessionmaker[AsyncSession]):
    while True:
        async with session_pool() as session:
            try:
                await notify_expiring_trials(session, bot)
                await notify_expiring_subscriptions(session, bot)
                await enforce_expirations(session, bot)
                await session.commit()
            except Exception as e:
                logger.exception("billing_notifier error: %s", e)
                await session.rollback()
        await asyncio.sleep(NOTIFY_CHECK_INTERVAL_MIN * 60)


if __name__ == "__main__":

    def custom_loop():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.set_exception_handler(handle_uncaught_exception)
        return loop

    loop = custom_loop()

try:
    loop.run_until_complete(main())
except KeyboardInterrupt:
    logger.info("🛑 Bot stopped by user (KeyboardInterrupt)")
finally:
    # 🧩 Завершаем Hawk, чтобы не было "Task was destroyed but it is pending!"
    try:
        from core.monitoring.hawk_setup import close_hawk

        asyncio.run(close_hawk())
    except Exception as e:
        logger.warning(f"⚠️ Failed to close Hawk cleanly: {e}")

    loop.close()
