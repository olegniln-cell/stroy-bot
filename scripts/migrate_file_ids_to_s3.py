# scripts/migrate_file_ids_to_s3.py
import os
import io
import logging
import asyncio
from aiogram import Bot
from database import init_db, async_session_maker
from storage.s3 import upload_bytes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("migrate")

BOT_TOKEN = os.getenv("BOT_TOKEN")


async def run():
    await init_db()
    bot = Bot(BOT_TOKEN)
    async with async_session_maker() as session:
        q = await session.execute(
            "SELECT * FROM files WHERE file_id IS NOT NULL AND s3_key IS NULL"
        )
        rows = q.fetchall()
        for row in rows:
            try:
                file_id = row.file_id
                file_info = await bot.get_file(file_id)
                buf = io.BytesIO()
                await file_info.download(out=buf)
                buf.seek(0)
                key = f"project/{row.id}/{file_info.file_path.split('/')[-1]}"
                upload_bytes(buf.read(), key)
                # обновить запись в БД
                await session.execute(
                    "UPDATE files SET s3_key = :k, storage_provider = :p WHERE id = :id",
                    {"k": key, "p": os.getenv("S3_PROVIDER", "minio"), "id": row.id},
                )
                await session.commit()
                logger.info("Migrated file %s -> %s", row.id, key)
            except Exception as e:
                logger.exception("Error migrating file %s: %s", row.id, e)
    await bot.session.close()


if __name__ == "__main__":
    asyncio.run(run())
