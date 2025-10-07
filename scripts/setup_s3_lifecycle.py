# scripts/setup_s3_lifecycle.py
import os
from storage.s3 import get_s3_client


def create_lifecycle(bucket_name: str, compress_days: int = 30, delete_days: int = 90):
    s3 = get_s3_client()

    # Для AWS S3: lifecycle configuration
    lifecycle = {
        "Rules": [
            {
                "ID": "compress-after-30",
                "Prefix": "",
                "Status": "Enabled",
                "Filter": {"Prefix": "project/"},
                "Transitions": [
                    # Здесь можно переводить в Glacier (т.о. "архивировать")
                    {"Days": compress_days, "StorageClass": "STANDARD_IA"}
                ],
                "NoncurrentVersionExpiration": {"NoncurrentDays": delete_days},
            },
            {
                "ID": "delete-after-90",
                "Prefix": "",
                "Status": "Enabled",
                "Filter": {"Prefix": ""},
                "Expiration": {"Days": delete_days},
            },
        ]
    }

    # MinIO поддерживает PutBucketLifecycleConfiguration
    s3.put_bucket_lifecycle_configuration(
        Bucket=bucket_name, LifecycleConfiguration=lifecycle
    )
    print("Lifecycle applied to bucket:", bucket_name)


if __name__ == "__main__":
    bucket = os.getenv("S3_BUCKET_NAME")
    create_lifecycle(bucket)
