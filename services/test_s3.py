# scripts/test_s3.py
import asyncio
from storage.s3 import generate_presigned_put_url, generate_presigned_get_url
import aiohttp
import uuid


async def main():
    # Генерим случайное имя файла
    object_name = f"test/{uuid.uuid4()}.txt"

    # Получаем URL для загрузки
    put_url = await generate_presigned_put_url(object_name)
    print("PUT URL:", put_url)

    # Загружаем файл через aiohttp
    async with aiohttp.ClientSession() as session:
        async with session.put(put_url, data=b"Hello from test_s3!") as resp:
            print("Upload status:", resp.status)

    # Получаем URL для скачивания
    get_url = await generate_presigned_get_url(object_name)
    print("GET URL:", get_url)

    # Скачиваем файл
    async with aiohttp.ClientSession() as session:
        async with session.get(get_url) as resp:
            data = await resp.text()
            print("Downloaded content:", data)


if __name__ == "__main__":
    asyncio.run(main())
