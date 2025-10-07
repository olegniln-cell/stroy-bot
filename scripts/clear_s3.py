from storage.s3 import get_s3_client, S3_BUCKET_NAME


def clear_bucket(bucket_name: str = S3_BUCKET_NAME, keep_uploads: bool = False):
    s3 = get_s3_client()
    print(f"🧹 Чистим bucket: {bucket_name} (keep_uploads={keep_uploads})")

    try:
        while True:
            objects = s3.list_objects_v2(Bucket=bucket_name)
            if "Contents" not in objects:
                print("✅ Bucket уже пуст")
                break

            if keep_uploads:
                keys = [
                    {"Key": obj["Key"]}
                    for obj in objects["Contents"]
                    if not obj["Key"].startswith("uploads/")
                ]
            else:
                keys = [{"Key": obj["Key"]} for obj in objects["Contents"]]

            if not keys:
                print("✅ Удалять нечего (uploads/ сохранены)")
                break

            s3.delete_objects(Bucket=bucket_name, Delete={"Objects": keys})
            print(f"✅ Удалено {len(keys)} объектов")

            if not objects.get("IsTruncated"):
                break

    except Exception as e:
        print(f"❌ Ошибка при очистке: {e}")


def main():
    import sys

    keep_uploads = "--keep-uploads" in sys.argv
    clear_bucket(keep_uploads=keep_uploads)


if __name__ == "__main__":
    main()
