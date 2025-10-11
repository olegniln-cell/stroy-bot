# services/notifications/tasks.py
from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession
from models.user import User
from models.task import Task
from utils.enums import UserRole
import logging

logger = logging.getLogger(__name__)

TASK_MESSAGES = {
    "new_task": "🆕 Новая задача: *{title}*\nПроект: {project}\nОписание: {description}",
    "taken": "🛠 {worker_name} взял задачу *{title}* в работу.",
    "completed": "✅ {worker_name} завершил задачу *{title}*.",
    "approved": "🎯 Задача *{title}* проверена и одобрена.",
    "rejected": "⚠️ Задача *{title}* отправлена на доработку.",
    "deadline_soon": "⏰ Напоминание: срок задачи *{title}* — сегодня!",
    "deadline_overdue": "🚨 Просрочена задача *{title}* (срок: {deadline}).",
}


async def _get_managers_and_foremen(session: AsyncSession, company_id: int):
    """Возвращает менеджеров и прорабов компании."""
    result = await session.execute(
        User.__table__.select().where(User.company_id == company_id)
    )
    users = [User(**row) for row in result.mappings()]
    return [
        u for u in users if u.role in (UserRole.manager.value, UserRole.foreman.value)
    ]


async def send_task_notification(
    bot: Bot,
    session: AsyncSession,
    task: Task,
    template_key: str,
    actor_name: str | None = None,
):
    """Отправляет уведомления нужным участникам по событию."""
    text = TASK_MESSAGES.get(template_key, "ℹ️ Обновление задачи.").format(
        title=task.title,
        project=getattr(task, "project_id", "—"),
        description=task.description or "—",
        worker_name=actor_name or "Исполнитель",
        deadline=getattr(task, "deadline", "не задан"),
    )

    recipients = []

    if template_key == "new_task":
        # Исполнитель
        if task.user_id:
            worker = await session.get(User, task.user_id)
            if worker and worker.tg_id:
                recipients.append(worker.tg_id)
    elif template_key in ("taken", "completed", "approved", "rejected"):
        # Менеджеры и прорабы
        managers = await _get_managers_and_foremen(session, task.company_id)
        recipients.extend([u.tg_id for u in managers if u.tg_id])
    elif template_key.startswith("deadline_"):
        # Исполнителю
        worker = await session.get(User, task.user_id)
        if worker and worker.tg_id:
            recipients.append(worker.tg_id)

    for tg_id in set(recipients):
        try:
            await bot.send_message(chat_id=tg_id, text=text, parse_mode="Markdown")
        except Exception as e:
            logger.error(
                f"Ошибка при отправке уведомления {template_key} пользователю {tg_id}: {e}"
            )
