# handlers/help.py
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from models.user import User
from sqlalchemy.ext.asyncio import AsyncSession
from utils.enums import UserRole

router = Router()


@router.message(Command("help"))
async def cmd_help(message: Message, session: AsyncSession, user: User):
    commands = ["/start – регистрация или начало работы", "/help – показать справку"]

    if not user.company_id:
        commands.append("/create_company <название> – создать компанию")
        commands.append(
            "/join <ID> [роль] – присоединиться к компании (роль: рабочий/бригадир)"
        )

    if user.role == UserRole.manager:
        commands += [
            "/invite – получить код-приглашение",
            "/add_project – добавить проект",
            "/add_task – добавить задачу",
            "/show_projects – посмотреть проекты",
            "/reassign_task – переназначить задачу",
            "/reports – посмотреть отчёты",
        ]

    if user.role == UserRole.foreman:
        commands += [
            "/add_project – добавить проект",
            "/add_task – добавить задачу",
            "/show_projects – посмотреть проекты",
            "/my_tasks – показать мои задачи",
            "/reassign_task – переназначить задачу",
            "/set_status – изменить статус задачи",
        ]

    if user.role == UserRole.worker:
        commands += [
            "/my_tasks – показать мои задачи",
            "/set_status – изменить статус задачи",
        ]

    if user.role == UserRole.admin:
        commands += [
            "/list_companies – список компаний",
            "/force_plan <company_id> <plan_code> – назначить тариф",
            "/force_extend_trial <company_id> <days> – продлить триал",
        ]

    await message.answer("Доступные команды:\n" + "\n".join(commands))
