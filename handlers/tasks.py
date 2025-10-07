from aiogram import Router, types
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from models.user import User
from models.project import Project
from services.tasks import create_task, get_my_tasks
from services.projects import get_project_by_id_and_company
from utils.helpers import format_tasks_list
from utils.decorators import is_manager_or_foreman
from services.audit import log_action
import logging  # Импортируем logging

# Настраиваем логирование
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)

router = Router()


@router.message(Command("add_task"))
@is_manager_or_foreman
async def add_task_cmd(message: types.Message, session: AsyncSession, user: User):
    logging.debug(f"Получен запрос на создание задачи от пользователя {user.id}")

    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.answer(
            "Пожалуйста, укажите ID проекта, заголовок и описание задачи."
        )
        return

    try:
        project_id = int(args[1])
        title = args[2].strip()
        description = " ".join(args[3:]) if len(args) > 3 else ""
    except (ValueError, IndexError):
        await message.answer("Неверный формат команды. ID проекта должен быть числом.")
        return

    try:
        # Проверяем существование проекта
        project = await get_project_by_id_and_company(
            session, project_id, user.company_id
        )
        if not project:
            await message.answer("Проект не найден или не принадлежит вашей компании.")
            return

        # Создаем задачу
        task = await create_task(
            session, title, description, project_id, user.company_id, user.id
        )

        # Добавляем логирование после успешного создания задачи
        await log_action(
            session,
            actor_user_id=user.id,
            actor_tg_id=user.tg_id,
            action="create_task",
            entity_type="Task",
            entity_id=task.id,
            payload={
                "title": task.title,
                "description": task.description,
                "project_id": project_id,
            },
        )

        logging.info(f"Задача успешно создана: ID={task.id}")
        await message.answer(
            f"Задача '{task.title}' успешно создана в проекте '{project.name}'!"
        )
    except Exception as e:
        logging.error(f"Ошибка при создании задачи: {str(e)}")
        await message.answer("Произошла ошибка при создании задачи.")


@router.message(Command("my_tasks"))
async def my_tasks_cmd(message: types.Message, session: AsyncSession, user: User):
    if not user.company_id:
        await message.answer("Вы не состоите в компании.")
        return

    tasks = await get_my_tasks(session, user.id)
    if not tasks:
        await message.answer("У вас пока нет задач.")
        return

    for task in tasks:
        task.project = await session.get(Project, task.project_id)

    text = format_tasks_list(tasks)
    await message.answer(text)
