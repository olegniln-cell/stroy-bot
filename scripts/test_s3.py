import uuid
from storage.s3 import get_s3_client, ensure_bucket_exists, S3_BUCKET_NAME


def main():
    print(f"=== Начинаем тест S3. Проверяем bucket: {S3_BUCKET_NAME} ===")

    s3 = get_s3_client()
    if not ensure_bucket_exists(S3_BUCKET_NAME):
        print("❌ Не удалось создать или найти bucket")
        return

    test_key = f"test/{uuid.uuid4()}.txt"
    test_content = b"Hello from test script!"

    # 1. Загружаем файл
    try:
        s3.put_object(Bucket=S3_BUCKET_NAME, Key=test_key, Body=test_content)
        print(f"✅ Файл загружен: {test_key}")
    except Exception as e:
        print(f"❌ Ошибка загрузки: {e}")
        return

    # 2. Скачиваем файл обратно
    try:
        response = s3.get_object(Bucket=S3_BUCKET_NAME, Key=test_key)
        downloaded = response["Body"].read()
        if downloaded == test_content:
            print("✅ Файл успешно скачан и совпадает с оригиналом")
        else:
            print("❌ Файл скачан, но данные не совпадают")
    except Exception as e:
        print(f"❌ Ошибка скачивания: {e}")


if __name__ == "__main__":
    main()
