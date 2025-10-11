# services/notifications/scheduler.py
import asyncio
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.task import Task
from utils.enums import TaskStatus
from services.notifications.tasks import send_task_notification

logger = logging.getLogger(__name__)

CHECK_INTERVAL_MINUTES = 10  # как часто проверять
DEADLINE_SOON_HOURS = 24  # за сколько часов до дедлайна напоминать


async def check_deadlines(bot, session: AsyncSession):
    """Проверяет дедлайны и рассылает уведомления."""
    now = datetime.utcnow()
    soon = now + timedelta(hours=DEADLINE_SOON_HOURS)

    # 1️⃣ Задачи со сроком сегодня
    soon_tasks_q = await session.execute(
        select(Task).where(
            Task.status.in_([TaskStatus.todo.value, TaskStatus.in_progress.value]),
            Task.deleted_at.is_(None),
            Task.company_id.isnot(None),
            Task.created_at
            <= soon,  # можно заменить на Task.deadline, если появится поле
        )
    )
    soon_tasks = soon_tasks_q.scalars().all()

    # 2️⃣ Просроченные задачи
    overdue_tasks_q = await session.execute(
        select(Task).where(
            Task.status.in_([TaskStatus.todo.value, TaskStatus.in_progress.value]),
            Task.deleted_at.is_(None),
            Task.company_id.isnot(None),
            Task.created_at
            < now - timedelta(days=3),  # временно, пока нет Task.deadline
        )
    )
    overdue_tasks = overdue_tasks_q.scalars().all()

    # 3️⃣ Рассылка
    for task in soon_tasks:
        await send_task_notification(bot, session, task, "deadline_soon")
    for task in overdue_tasks:
        await send_task_notification(bot, session, task, "deadline_overdue")

    if soon_tasks or overdue_tasks:
        await session.commit()
        logger.info(
            f"🔔 Отправлено уведомлений: сегодня={len(soon_tasks)}, просрочено={len(overdue_tasks)}"
        )


def start_scheduler(bot, session_factory):
    """Запускает фоновый планировщик напоминаний."""
    scheduler = AsyncIOScheduler(timezone="UTC")

    async def job_wrapper():
        async with session_factory() as session:
            try:
                await check_deadlines(bot, session)
            except Exception as e:
                logger.exception(
                    f"Ошибка при выполнении фоновой проверки дедлайнов: {e}"
                )

    scheduler.add_job(
        lambda: asyncio.create_task(job_wrapper()),
        trigger="interval",
        minutes=CHECK_INTERVAL_MINUTES,
        id="deadline_checker",
        replace_existing=True,
    )

    scheduler.start()
    logger.info(f"🕒 Scheduler started — interval {CHECK_INTERVAL_MINUTES} min")
