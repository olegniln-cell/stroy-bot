# handlers/tasks.py
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from models.user import User
from models.project import Project
from services.tasks import (
    create_task,
    get_my_tasks,
    set_task_status,
    get_task_by_id_and_company,
)
from services.projects import get_project_by_id_and_company
from services.audit import log_action
from utils.decorators import is_manager_or_foreman
from utils.enums import TaskStatus
import logging

router = Router()
logger = logging.getLogger(__name__)

# ========== HELPERS ==========


def task_inline_keyboard(task_id: int, status: str) -> InlineKeyboardMarkup:
    """Создаёт клавиатуру под задачей в зависимости от статуса."""
    buttons = []

    if status == TaskStatus.todo.value:
        buttons.append(
            [
                InlineKeyboardButton(
                    text="✅ Взять в работу", callback_data=f"take_task:{task_id}"
                )
            ]
        )
    elif status == TaskStatus.in_progress.value:
        buttons.append(
            [
                #        InlineKeyboardButton(text="📎 Прикрепить фото", callback_data=f"attach_file:{task_id}"),
                InlineKeyboardButton(
                    text="✅ Завершить", callback_data=f"complete_task:{task_id}"
                ),
            ]
        )
    elif status == TaskStatus.ready.value:
        buttons.append(
            [
                InlineKeyboardButton(
                    text="🔍 Проверить", callback_data=f"review_task:{task_id}"
                )
            ]
        )

    # Общие кнопки
    buttons.append(
        [
            InlineKeyboardButton(
                text="📄 Подробнее", callback_data=f"details_task:{task_id}"
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ========== COMMAND HANDLERS ==========


@router.message(Command("add_task"))
@is_manager_or_foreman
async def add_task_cmd(message: types.Message, session: AsyncSession, user: User):
    logger.debug(f"Получен запрос на создание задачи от пользователя {user.id}")

    args = message.text.split(maxsplit=3)
    if len(args) < 3:
        await message.answer(
            "Используй формат: /add_task <project_id> <заголовок> [описание]"
        )
        return

    try:
        project_id = int(args[1])
        title = args[2].strip()
        description = args[3].strip() if len(args) > 3 else ""
    except (ValueError, IndexError):
        await message.answer("Неверный формат. ID проекта должен быть числом.")
        return

    project = await get_project_by_id_and_company(session, project_id, user.company_id)
    if not project:
        await message.answer("Проект не найден или не принадлежит вашей компании.")
        return

    task = await create_task(
        session, title, description, project_id, user.company_id, user.id
    )

    await log_action(
        session,
        actor_user_id=user.id,
        actor_tg_id=user.tg_id,
        action="create_task",
        entity_type="Task",
        entity_id=task.id,
        payload={"title": task.title, "project_id": project_id},
    )

    await message.answer(
        f"✅ Задача *{task.title}* создана в проекте *{project.name}*.",
        reply_markup=task_inline_keyboard(task.id, task.status),
        parse_mode="Markdown",
    )


@router.message(Command("my_tasks"))
async def my_tasks_cmd(message: types.Message, session: AsyncSession, user: User):
    """Показывает все задачи пользователя с inline-кнопками."""
    if not user.company_id:
        await message.answer("Вы не состоите в компании.")
        return

    tasks = await get_my_tasks(session, user.id)
    if not tasks:
        await message.answer("У вас пока нет задач.")
        return

    for task in tasks:
        task.project = await session.get(Project, task.project_id)

        text = (
            f"📋 *{task.title}*\n"
            f"Проект: {task.project.name}\n"
            f"Статус: {task.status}\n"
            f"Описание: {task.description or '—'}"
        )

        await message.answer(
            text,
            reply_markup=task_inline_keyboard(task.id, task.status),
            parse_mode="Markdown",
        )


# ========== CALLBACKS ==========


@router.callback_query(lambda c: c.data.startswith("take_task:"))
async def take_task_cb(callback: CallbackQuery, session: AsyncSession, user: User):
    """Рабочий берёт задачу в работу."""
    task_id = int(callback.data.split(":")[1])
    task = await set_task_status(
        session, task_id, TaskStatus.in_progress.value, user.company_id
    )
    if not task:
        await callback.answer("❌ Задача не найдена или недоступна.")
        return

    await session.commit()

    if not task:
        await callback.answer("❌ Задача не найдена или недоступна.")
        return

    await callback.message.edit_text(
        f"🛠 Ты взял задачу *{task.title}* в работу.",
        reply_markup=task_inline_keyboard(task.id, task.status),
        parse_mode="Markdown",
    )

    await log_action(
        session,
        actor_user_id=user.id,
        actor_tg_id=user.tg_id,
        action="take_task",
        entity_type="Task",
        entity_id=task.id,
        payload={"status": task.status},
    )
    await session.commit()

    await callback.answer("Задача взята в работу ✅")


@router.callback_query(lambda c: c.data.startswith("complete_task:"))
async def complete_task_cb(callback: CallbackQuery, session: AsyncSession, user: User):
    """Рабочий завершает задачу."""
    task_id = int(callback.data.split(":")[1])
    task = await set_task_status(
        session, task_id, TaskStatus.ready.value, user.company_id
    )
    await session.commit()

    if not task:
        await callback.answer("Задача не найдена.")
        return

    await callback.message.edit_text(
        f"✅ Задача *{task.title}* завершена и отправлена на проверку.",
        reply_markup=task_inline_keyboard(task.id, TaskStatus.ready.value),
        parse_mode="Markdown",
    )

    await log_action(
        session,
        user.id,
        user.tg_id,
        "complete_task",
        "Task",
        task.id,
        {"status": task.status},
    )
    await callback.answer("Отправлено на проверку 🔍")


@router.callback_query(lambda c: c.data.startswith("details_task:"))
async def details_task_cb(callback: CallbackQuery, session: AsyncSession, user: User):
    """Показывает подробности задачи."""
    task_id = int(callback.data.split(":")[1])
    task = await get_task_by_id_and_company(session, task_id, user.company_id)
    if not task:
        await callback.answer("Задача не найдена.")
        return

    project = await session.get(Project, task.project_id)
    text = (
        f"📄 *{task.title}*\n"
        f"Проект: {project.name}\n"
        f"Статус: {task.status}\n"
        f"Описание: {task.description or '—'}\n"
        f"Создана: {task.created_at.strftime('%d.%m.%Y %H:%M')}"
    )

    await callback.message.edit_text(
        text,
        reply_markup=task_inline_keyboard(task.id, task.status),
        parse_mode="Markdown",
    )
    await callback.answer()
