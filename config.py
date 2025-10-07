import os
from dotenv import load_dotenv

load_dotenv(".env.local", override=True)
load_dotenv(".env")

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")


# Переменные для S3 / MinIO
S3_ACCESS_KEY_ID = os.getenv("S3_ACCESS_KEY_ID")
S3_SECRET_ACCESS_KEY = os.getenv("S3_SECRET_ACCESS_KEY")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
S3_REGION = os.getenv("S3_REGION", "us-east-1")  # Укажите свой регион
S3_ENDPOINT_URL = os.getenv(
    "S3_ENDPOINT_URL", None
)  # Для MinIO или другого S3-совместимого сервиса


# Сколько дней даём на триал по умолчанию
TRIAL_DAYS_DEFAULT = 14
# За сколько дней до окончания слать напоминания
BILLING_REMIND_DAYS = 3
# Если нужно мягко отключать доступ после просрочки (True = закрываем доступ сразу по expires_at)
DISABLE_ON_EXPIRE = True
# Телеграм ID глобальных админов (если вдруг понадобится вне ролей)
GLOBAL_ADMIN_TG_IDS = []  # например: [123456789]
# Периодичность проверки уведомлений (если используешь APScheduler/cron)
NOTIFY_CHECK_INTERVAL_MIN = 30
