from aiogram import Router, types
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from models.user import User
from services.tasks import set_task_status

router = Router()


# --- ИЗМЕНЕНИЕ: set_status_cmd ---
# Добавляем user.company_id в вызов сервиса
@router.message(Command("set_status"))
async def set_status_cmd(message: types.Message, session: AsyncSession, user: User):
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.answer(
            "Неверный формат команды. Использование: `/set_status <ID задачи> <Статус>`"
        )
        return

    try:
        task_id = int(args[1])
        status = args[2]
    except ValueError:
        await message.answer("ID задачи должен быть числом.")
        return

    task = await set_task_status(
        session, task_id, status, user.company_id
    )  # <- Добавили company_id
    if task:
        await message.answer(
            f"Статус задачи '{task.title}' успешно изменён на '{task.status}'."
        )
    else:
        await message.answer("Задача с таким ID не найдена.")
