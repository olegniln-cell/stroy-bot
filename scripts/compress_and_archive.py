# scripts/compress_and_archive.py
import os
import logging
from datetime import datetime, timedelta
from sqlalchemy import select
from storage.s3 import get_object_bytes, upload_bytes, zip_bytes, delete_object
from database import async_session_maker, init_db
from models import File  # предполагаем модель File

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("compress")


async def run():
    await init_db()
    cutoff = datetime.utcnow() - timedelta(
        days=int(os.getenv("FILES_COMPRESS_DAYS", 30))
    )
    async with async_session_maker() as session:  # если у тебя async_session_maker определён
        q = await session.execute(
            select(File).where(
                File.created_at <= cutoff,
                File.s3_key.isnot(None),
                File.archived_at is None,
            )
        )
        files = q.scalars().all()
        for f in files:
            try:
                data = get_object_bytes(f.s3_key)
                if not data:
                    logger.warning("No data for %s", f.s3_key)
                    continue
                # простая архивация: упакуем в zip под тем же именем
                zip_data = zip_bytes({f.filename or "file": data})
                new_key = f"{f.s3_key}.zip"
                upload_bytes(
                    zip_data,
                    new_key,
                    content_type="application/zip",
                    storage_class="STANDARD_IA",
                )
                # удаляем старый объект
                delete_object(f.s3_key)
                # сохраняем в БД новый ключ и помечаем archived_at
                f.s3_key = new_key
                f.storage_class = "STANDARD_IA"
                f.archived_at = datetime.utcnow()
                session.add(f)
                await session.commit()
                logger.info("Archived file %s -> %s", f.id, new_key)
            except Exception as e:
                logger.exception("Failed to archive file %s: %s", f.id, e)


if __name__ == "__main__":
    import asyncio

    asyncio.run(run())
