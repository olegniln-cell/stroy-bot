# handlers/review.py
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from models.user import User
from services.tasks import get_task_by_id_and_company, set_task_status
from services.notifications.tasks import send_task_notification
from services.audit import log_action
from utils.enums import TaskStatus
from utils.decorators import is_manager_or_foreman
import logging

router = Router()
logger = logging.getLogger(__name__)


# ======== HELPERS ==========
def review_keyboard(task_id: int) -> InlineKeyboardMarkup:
    """Клавиатура проверки задачи."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Принять", callback_data=f"approve_task:{task_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔁 На доработку", callback_data=f"reject_task:{task_id}"
                )
            ],
        ]
    )


# ======== HANDLERS ==========


@router.message(Command("review_task"))
@is_manager_or_foreman
async def review_task_cmd(message: types.Message, session: AsyncSession, user: User):
    """Ручная проверка по ID задачи."""
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Используй: /review_task <task_id>")
        return

    try:
        task_id = int(args[1])
    except ValueError:
        await message.answer("ID задачи должен быть числом.")
        return

    task = await get_task_by_id_and_company(session, task_id, user.company_id)
    if not task:
        await message.answer("Задача не найдена.")
        return

    await message.answer(
        f"Проверка задачи: *{task.title}*\nОписание: {task.description or '—'}",
        reply_markup=review_keyboard(task.id),
        parse_mode="Markdown",
    )


# ======== CALLBACKS ==========


@router.callback_query(lambda c: c.data.startswith("approve_task:"))
async def approve_task_cb(
    callback: CallbackQuery, session: AsyncSession, user: User, bot
):
    """Принимаем задачу."""
    task_id = int(callback.data.split(":")[1])
    task = await set_task_status(
        session, task_id, TaskStatus.ready.value, user.company_id
    )
    await session.commit()

    await log_action(
        session,
        user.id,
        user.tg_id,
        "approve_task",
        "Task",
        task_id,
        {"status": task.status},
    )
    await send_task_notification(
        bot, session, task, "approved", user.username or user.tg_id
    )

    await callback.message.edit_text(
        f"🎯 Задача *{task.title}* принята.",
        parse_mode="Markdown",
    )
    await callback.answer("Задача принята ✅")


@router.callback_query(lambda c: c.data.startswith("reject_task:"))
async def reject_task_cb(
    callback: CallbackQuery, session: AsyncSession, user: User, bot
):
    """Отправляем задачу на доработку."""
    task_id = int(callback.data.split(":")[1])
    task = await set_task_status(
        session, task_id, TaskStatus.in_progress.value, user.company_id
    )
    await session.commit()

    await log_action(
        session,
        user.id,
        user.tg_id,
        "reject_task",
        "Task",
        task_id,
        {"status": task.status},
    )
    await send_task_notification(
        bot, session, task, "rejected", user.username or user.tg_id
    )

    await callback.message.edit_text(
        f"⚠️ Задача *{task.title}* отправлена на доработку.",
        parse_mode="Markdown",
    )
    await callback.answer("Отправлено на доработку 🔁")
