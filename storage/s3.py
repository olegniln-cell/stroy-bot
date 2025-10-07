import os
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from uuid import uuid4

S3_ACCESS_KEY_ID = os.getenv("S3_ACCESS_KEY_ID")
S3_SECRET_ACCESS_KEY = os.getenv("S3_SECRET_ACCESS_KEY")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
S3_REGION = os.getenv("S3_REGION", "us-east-1")
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL", "http://minio:9000")


def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT_URL,
        aws_access_key_id=S3_ACCESS_KEY_ID,
        aws_secret_access_key=S3_SECRET_ACCESS_KEY,
        region_name=S3_REGION,
        config=Config(signature_version="s3v4"),
    )


def ensure_bucket_exists(bucket_name: str = S3_BUCKET_NAME):
    """
    Проверяет, что bucket существует. Если нет — создаёт.
    Работает и с MinIO, и с AWS S3.
    """
    client = get_s3_client()
    try:
        client.head_bucket(Bucket=bucket_name)
        print(f"✅ Bucket {bucket_name} существует")
        return True
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        if code in ("404", "NoSuchBucket"):
            # создаём bucket
            try:
                if S3_ENDPOINT_URL and "minio" in S3_ENDPOINT_URL:
                    # MinIO не любит LocationConstraint
                    client.create_bucket(Bucket=bucket_name)
                else:
                    if S3_REGION == "us-east-1":
                        client.create_bucket(Bucket=bucket_name)
                    else:
                        client.create_bucket(
                            Bucket=bucket_name,
                            CreateBucketConfiguration={"LocationConstraint": S3_REGION},
                        )
                print(f"✅ Bucket {bucket_name} создан")
                return True
            except Exception as ce:
                print(f"❌ Ошибка при создании bucket {bucket_name}: {ce}")
                return False
        elif code in ("403", "AccessDenied"):
            # Может быть, bucket есть, но доступ ограничен
            print(f"⚠️ Bucket {bucket_name} есть, но нет доступа (403)")
            return True
        else:
            print(f"❌ Ошибка доступа к bucket {bucket_name}: {e}")
            return False


def generate_presigned_put_url(key: str = None, expires_in: int = 3600) -> str:
    """
    Генерация временной ссылки для загрузки файла (PUT).
    """
    if key is None:
        key = f"uploads/{uuid4()}.bin"

    client = get_s3_client()
    return client.generate_presigned_url(
        "put_object",
        Params={"Bucket": S3_BUCKET_NAME, "Key": key},
        ExpiresIn=expires_in,
    )


def generate_presigned_get_url(key: str, expires_in: int = 3600) -> str:
    """
    Генерация временной ссылки для скачивания файла (GET).
    """
    client = get_s3_client()
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": S3_BUCKET_NAME, "Key": key},
        ExpiresIn=expires_in,
    )
