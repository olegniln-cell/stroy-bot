from aiogram import Router, types
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from models.user import User
from services.tasks import reassign_task
from utils.decorators import is_manager_or_foreman

router = Router()


@router.message(Command("reassign_task"))
@is_manager_or_foreman
async def reassign_task_cmd(message: types.Message, session: AsyncSession, user: User):
    args = message.text.split()
    if len(args) < 3:
        await message.answer(
            "Неверный формат команды. Использование: `/reassign_task <ID задачи> <ID пользователя>`"
        )
        return

    try:
        task_id = int(args[1])
        new_assignee_id = int(args[2])
    except ValueError:
        await message.answer("ID задачи и пользователя должны быть числами.")
        return

    task = await reassign_task(
        session, task_id, new_assignee_id, user.company_id
    )  # <- Добавили company_id
    if task:

        await message.answer(
            f"Задача '{task.title}' успешно переназначена пользователю с ID {new_assignee_id}."
        )
    else:
        await message.answer("Задача с таким ID не найдена.")
