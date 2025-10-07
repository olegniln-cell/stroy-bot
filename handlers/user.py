# handlers/user.py

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from services.users import get_user_by_tg_id

router = Router()


@router.message(Command("me"))
async def me_cmd(message: Message, session: AsyncSession):
    user = await get_user_by_tg_id(session, message.from_user.id)
    if not user:
        await message.answer("Вы не зарегистрированы. Используйте /start")
    else:
        await message.answer(
            f"Ваш ID: {user.id}\n"
            f"Роль: {user.role}\n"
            f"Компания ID: {user.company_id}"
        )
