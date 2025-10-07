from aiogram import Router, types
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from models.user import User
from services.projects import create_project, get_projects_by_company_id
from utils.decorators import is_manager, is_manager_or_foreman
from services.audit import log_action
import logging

# Настраиваем логирование
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)

router = Router()


@router.message(Command("add_project"))
@is_manager
async def add_project_cmd(message: types.Message, session: AsyncSession, user: User):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "Пожалуйста, укажите название проекта.\nИспользование: `/add_project <НазваниеПроекта>`"
        )
        return

    project_name = args[1].strip()

    try:
        project = await create_project(session, project_name, user.company_id)
        logging.debug(
            f"Создан проект: ID={project.id}, Name={project.name}, CompanyID={project.company_id}"
        )

        # Добавляем логирование
        await log_action(
            session,
            actor_user_id=user.id,
            actor_tg_id=user.tg_id,
            action="create_project",
            entity_type="Project",
            entity_id=project.id,
            payload={"name": project.name, "company_id": project.company_id},
        )

        await message.answer(
            f"Проект '{project.name}' успешно добавлен! ID: {project.id}"
        )
    except Exception as e:
        logging.error(f"Ошибка при создании проекта: {str(e)}")
        await message.answer("Произошла ошибка при создании проекта")


@router.message(Command("show_projects"))
@is_manager_or_foreman
async def show_projects_cmd(message: types.Message, session: AsyncSession, user: User):
    logging.debug(f"Получение проектов для компании: {user.company_id}")

    try:
        projects = await get_projects_by_company_id(session, user.company_id)
        logging.debug(f"Найдено проектов: {len(projects)}")

        if not projects:
            await message.answer("Проекты не найдены.")
            return

        projects_list = "\n".join(
            [f"{p.id}. {p.name} (CompanyID: {p.company_id})" for p in projects]
        )
        await message.answer(f"Список ваших проектов:\n{projects_list}")
    except Exception as e:
        logging.error(f"Ошибка при получении проектов: {str(e)}")
        await message.answer("Произошла ошибка при получении списка проектов")


@router.message(Command("list_projects_all"))
@is_manager
async def list_all_projects(message: types.Message, session: AsyncSession, user: User):
    try:
        # Получаем все проекты без фильтрации по компании
        result = await session.execute("SELECT id, name, company_id FROM projects")
        projects = result.fetchall()

        if not projects:
            await message.answer("В базе данных нет проектов")
            return

        projects_list = "\n".join(
            [f"{p[0]}. {p[1]} (CompanyID: {p[2]})" for p in projects]
        )
        await message.answer(f"Все проекты в базе:\n{projects_list}")
    except Exception as e:
        logging.error(f"Ошибка при получении всех проектов: {str(e)}")
        await message.answer("Произошла ошибка при получении всех проектов")
