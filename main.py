# -*- coding: utf-8 -*-
import os
import asyncio
import logging
from aiogram import Bot, Dispatcher
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

# middlewares
from middlewares.db_middleware import DbSessionMiddleware
from middlewares.role_checker import RoleCheckerMiddleware
from middlewares.company_middleware import CompanyMiddleware
from middlewares.subscription_checker import SubscriptionCheckerMiddleware
from middlewares.audit_middleware import AuditMiddleware

# jobs
from services.notify_jobs import (
    notify_expiring_trials,
    notify_expiring_subscriptions,
    enforce_expirations,
)
from services.seed import seed_plans

from fastapi import FastAPI
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST


# --- Hawk integration ---
import hawkcatcher



logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)



# --- Hawk integration ---
HAWK_TOKEN = os.getenv("HAWK_TOKEN")
ENV_MODE = os.getenv("ENV_MODE", "unknown")

if HAWK_TOKEN and ENV_MODE not in ("test", "ci"):
    try:
        hawkcatcher.init(HAWK_TOKEN)

        # Отправляем тестовое событие (новый синтаксис Hawk)
        hawkcatcher.send_event({
            "message": "Hawk integration test",
            "level": "info",
            "context": {"env": ENV_MODE}
        })
        logger.info("✅ Hawk Catcher initialized and test event sent.")
    except Exception as e:
        logger.warning(f"⚠️ Hawk initialization failed: {e}")
else:
    logger.info("ℹ️ Hawk Catcher disabled — no HAWK_TOKEN provided or ENV_MODE=test/ci.")




# --- Глобальный перехватчик необработанных ошибок ---
def handle_uncaught_exception(loop, context):
    msg = context.get("exception") or context.get("message")
    logger.error(f"🔥 Uncaught exception: {msg}")

    if HAWK_TOKEN:
        try:
            hawkcatcher.capture_exception(context.get("exception"))
        except Exception as e:
            logger.warning(f"⚠️ Failed to send exception to Hawk: {e}")


# --- Health-check server ---
async def start_health_server():

    async def handle_health(request):
        return web.Response(text="OK", status=200)

    async def handle_metrics(request):
        return web.Response(
            body=generate_latest(),
            content_type=CONTENT_TYPE_LATEST
        )

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
    logger.info("[BOOT] DB host: %s", db_host)
    logger.info("[BOOT] BOT_TOKEN: %s...", BOT_TOKEN[:6])

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

    # фоновый воркер
    asyncio.create_task(billing_notifier(bot, session_pool))

    logger.info("[INFO] Бот запускается...")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()
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
    loop.run_until_complete(main())
