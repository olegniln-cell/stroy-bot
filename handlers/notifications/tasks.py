# services/notifications/tasks.py
from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession
from models.user import User
from models.task import Task
from utils.enums import UserRole
import logging

logger = logging.getLogger(__name__)

# Все тексты можно будет потом вынести в messages.yaml
TASK_MESSAGES = {
    "new_task": "🆕 Новая задача: *{title}*\nПроект: {project}\nОписание: {description}",
    "taken": "🛠 {worker_name} взял задачу *{title}* в работу.",
    "completed": "✅ {worker_name} завершил задачу *{title}*.",
    "approved": "🎯 Задача *{title}* проверена и одобрена.",
    "rejected": "⚠️ Задача *{title}* отправлена на доработку.",
    "deadline_soon": "⏰ Напоминание: срок задачи *{title}* — сегодня!",
    "deadline_overdue": "🚨 Просрочена задача *{title}* (срок: {deadline}).",
}


async def _get_manager_and_foreman(session: AsyncSession, company_id: int):
    """Находим пользователей с ролями manager/foreman."""
    result = await session.execute(
        User.__table__.select().where(User.company_id == company_id)
    )
    users = result.fetchall()
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
    """Отправляет уведомления нужным участникам по типу события."""
    text = TASK_MESSAGES[template_key].format(
        title=task.title,
        project=task.project_id,
        description=task.description or "—",
        worker_name=actor_name or "Исполнитель",
        deadline=getattr(task, "deadline", "не задан"),
    )

    recipients = []

    # 1. Кому отправлять?
    if template_key == "new_task":
        # Рабочему, если назначен
        if task.user_id:
            user = await session.get(User, task.user_id)
            if user and user.tg_id:
                recipients.append(user.tg_id)
    elif template_key in ("taken", "completed", "approved", "rejected"):
        # Менеджеру и прорабу
        managers = await _get_manager_and_foreman(session, task.company_id)
        recipients.extend([u.tg_id for u in managers if u.tg_id])
    elif template_key in ("deadline_soon", "deadline_overdue"):
        # Исполнителю
        user = await session.get(User, task.user_id)
        if user and user.tg_id:
            recipients.append(user.tg_id)

    # 2. Отправляем сообщения
    for tg_id in recipients:
        try:
            await bot.send_message(chat_id=tg_id, text=text, parse_mode="Markdown")
        except Exception as e:
            logger.error(
                f"Не удалось отправить уведомление {template_key} пользователю {tg_id}: {e}"
            )
