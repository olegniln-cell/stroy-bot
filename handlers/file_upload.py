import uuid
import os
import logging
import aiohttp
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from models.project import Project
from models.task import Task
from models.user import User
from services.files import create_file
from storage.s3 import generate_presigned_put_url

router = Router()
logger = logging.getLogger(__name__)


class FileUploadState(StatesGroup):
    """Состояния для пошаговой загрузки файла."""

    waiting_for_project = State()
    waiting_for_task = State()
    waiting_for_file = State()


# -- Команды и хэндлеры --


@router.message(Command("upload", "add_file"))
async def cmd_upload_start(
    message: Message, state: FSMContext, session: AsyncSession, user: User
):
    """Начинает процесс загрузки файла."""
    # Получаем проекты для текущей компании пользователя
    projects_stmt = select(Project).where(Project.company_id == user.company_id)
    projects = (await session.execute(projects_stmt)).scalars().all()

    if not projects:
        await message.answer("В вашей компании нет проектов для загрузки файлов.")
        await state.clear()
        return

    buttons = [
        [InlineKeyboardButton(text=p.name, callback_data=f"upload_project:{p.id}")]
        for p in projects
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(
        "Выберите проект, к которому хотите прикрепить файл:", reply_markup=keyboard
    )
    await state.set_state(FileUploadState.waiting_for_project)


@router.callback_query(
    F.data.startswith("upload_project:"), FileUploadState.waiting_for_project
)
async def upload_select_project(
    callback_query: CallbackQuery, state: FSMContext, session: AsyncSession, user: User
):
    """Обрабатывает выбор проекта."""
    project_id = int(callback_query.data.split(":")[1])
    await state.update_data(project_id=project_id)

    tasks_stmt = select(Task).where(Task.project_id == project_id)
    tasks = (await session.execute(tasks_stmt)).scalars().all()

    if not tasks:
        await callback_query.message.edit_text(
            "В этом проекте нет задач для прикрепления файлов."
        )
        await state.clear()
        return

    buttons = [
        [
            InlineKeyboardButton(
                text=f"{t.title} (ID: {t.id})", callback_data=f"upload_task:{t.id}"
            )
        ]
        for t in tasks
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback_query.message.edit_text(
        "Выберите задачу, к которой прикрепить файл:", reply_markup=keyboard
    )
    await state.set_state(FileUploadState.waiting_for_task)


@router.callback_query(
    F.data.startswith("upload_task:"), FileUploadState.waiting_for_task
)
async def upload_select_task(callback_query: CallbackQuery, state: FSMContext):
    """Завершает выбор задачи и просит пользователя отправить файл."""
    task_id = int(callback_query.data.split(":")[1])
    await state.update_data(task_id=task_id)
    await callback_query.message.edit_text(
        "Отлично! Теперь отправьте мне файл (документ или фото)."
    )
    # Переходим в то же состояние, что и раньше, но теперь ждем именно файл
    await state.set_state(FileUploadState.waiting_for_file)


@router.message(FileUploadState.waiting_for_file, F.photo | F.document)
async def handle_file(
    message: Message, state: FSMContext, session: AsyncSession, user: User, bot: Bot
):
    """Обрабатывает загруженный файл и сохраняет его метаданные."""
    try:
        data = await state.get_data()
        task_id = data.get("task_id")

        # Получаем информацию о файле
        file_info = message.document if message.document else message.photo[-1]

        # Исправляем логику получения имени и MIME-типа
        if message.document:
            original_name = file_info.file_name
            mime_type = file_info.mime_type
        else:  # F.photo
            original_name = f"photo_{file_info.file_unique_id}.jpg"
            mime_type = "image/jpeg"  # У фото нет mime_type, поэтому задаем явно

        # Генерируем уникальный ключ для S3. Используем company_id для изоляции.
        file_extension = os.path.splitext(original_name)[1]
        s3_key = (
            f"company_{user.company_id}/task_{task_id}/{uuid.uuid4()}{file_extension}"
        )

        # Загружаем файл с серверов Telegram
        telegram_file = await bot.get_file(file_info.file_id)
        file_bytes = await bot.download_file(telegram_file.file_path)

        # Генерируем URL для загрузки файла
        presigned_url = await generate_presigned_put_url(s3_key)

        if not presigned_url:
            await message.answer(
                "Произошла ошибка при подготовке к загрузке. Пожалуйста, попробуйте снова."
            )
            await state.clear()
            return

        # Загружаем файл в S3
        async with aiohttp.ClientSession() as http_session:
            await http_session.put(presigned_url, data=file_bytes)

        # Сохраняем информацию о файле в БД
        new_file = await create_file(
            session=session,
            task_id=task_id,
            company_id=user.company_id,  # <--- ИСПРАВЛЕНО: Теперь передаем company_id
            uploader_id=user.id,
            original_name=original_name,
            mime_type=mime_type,
            size=file_info.file_size,
            s3_key=s3_key,
        )
        await message.answer(
            f"Файл '{new_file.original_name}' успешно прикреплён к задаче! ✅"
        )

    except Exception as e:
        logger.error(f"Error saving file info to DB: {e}")
        await message.answer(
            "Произошла ошибка при сохранении данных о файле. Пожалуйста, попробуйте снова."
        )
    finally:
        await state.clear()
