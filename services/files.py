from sqlalchemy.ext.asyncio import AsyncSession
from models.file import File
import uuid
from typing import Optional
import logging

logger = logging.getLogger(__name__)


async def create_file(
    session: AsyncSession,
    task_id: int,
    company_id: int,  # <-- Добавили этот аргумент
    uploader_id: int,
    original_name: str,
    mime_type: str,
    size: int,
    s3_key: str,
) -> File:
    """Создает новую запись о файле в базе данных.
    Args:
        session: Асинхронная сессия SQLAlchemy.
        task_id: ID задачи, к которой привязан файл.
        company_id: ID компании, к которой принадлежит файл.
        uploader_id: ID пользователя, который загрузил файл.
        original_name: Имя файла, которое было у пользователя.
        mime_type: MIME-тип файла.
        size: Размер файла в байтах.
        s3_key: Ключ файла в S3-хранилище.
    """
    new_file = File(
        task_id=task_id,
        company_id=company_id,  # <-- Используем новый аргумент
        uploader_id=uploader_id,
        original_name=original_name,
        mime_type=mime_type,
        size=size,
        s3_key=s3_key,
    )
    session.add(new_file)
    # commit/flush будет сделан в DbSessionMiddleware
    return new_file


async def get_file_by_id(session: AsyncSession, file_id: uuid.UUID) -> Optional[File]:
    """
    Получает файл по его UUID.
    """
    return await session.get(File, file_id)


async def delete_file(session: AsyncSession, file_id: uuid.UUID) -> bool:
    """
    Удаляет запись о файле из базы данных.

    Returns:
        True, если файл был найден и удален, False в противном случае.
    """
    file_to_delete = await get_file_by_id(session, file_id)
    if file_to_delete:
        await session.delete(file_to_delete)
        await session.commit()
        logger.info(f"File {file_id} deleted from database.")
        return True
    logger.warning(f"File {file_id} not found for deletion.")
    return False
