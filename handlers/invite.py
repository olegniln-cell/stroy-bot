# handlers/invite.py

from aiogram import Router, types
from aiogram.filters import Command
from models.user import User
from utils.decorators import is_manager

router = Router()


@router.message(Command("invite"))
@is_manager
async def create_invite_cmd(message: types.Message, user: User):
    if not user.company_id:
        await message.answer("Сначала создайте или присоединитесь к компании.")
        return

    # Временно используем company_id в качестве кода-приглашения.
    invite_code = user.company_id
    await message.answer(
        f"Ваш код-приглашение для сотрудников: `{invite_code}`\n"
        f"Попросите их использовать команду: `/join {invite_code}`"
    )
