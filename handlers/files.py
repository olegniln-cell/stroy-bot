from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from services.files import get_file_by_id
from storage.s3 import generate_presigned_get_url
from models.user import User
import uuid
import logging

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("get_file"))
async def get_file_cmd(message: Message, session: AsyncSession, user: User):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "Неверный формат команды. Используйте: /get_file <ID файла>"
        )
        return

    try:
        file_id = uuid.UUID(args[1])
    except ValueError:
        await message.answer("Неверный формат ID файла. ID должен быть UUID.")
        return

    file = await get_file_by_id(session, file_id)

    if not file:
        await message.answer("Файл с таким ID не найден.")
        return

    if file.company_id != user.company_id:
        await message.answer("У вас нет прав для доступа к этому файлу.")
        return

    presigned_url = await generate_presigned_get_url(file.s3_key)

    if presigned_url:
        await message.answer(
            f"Файл '{file.original_name}' доступен по временной ссылке:\n{presigned_url}\n\nСсылка будет активна 1 час."
        )
    else:
        await message.answer(
            "Произошла ошибка при получении ссылки на файл. Пожалуйста, попробуйте снова."
        )
