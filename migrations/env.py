from logging.config import fileConfig
from sqlalchemy import create_engine, pool  # Убрали асинхронные импорты
from alembic import context
import os

from models.base import Base

# ==============================================================================
# Удалены неиспользуемые импорты
# from sqlalchemy.ext.asyncio import create_async_engine
# import asyncio
# ==============================================================================

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


# ==============================================================================
# Упрощенная функция получения URL
def get_url():
    # 1️⃣ сначала читаем параметр, переданный через CLI: alembic -x db_url=...
    x_args = context.get_x_argument(as_dictionary=True)
    if "db_url" in x_args:
        return x_args["db_url"]

    # 2️⃣ затем стандартные приоритеты
    return (
        os.getenv("SYNC_TEST_DATABASE_URL")
        or os.getenv("SYNC_DATABASE_URL")
        or config.get_main_option("sqlalchemy.url")
        or os.getenv("DATABASE_URL")
    )


test_url = os.getenv("SYNC_TEST_DATABASE_URL") or os.getenv("DATABASE_URL")
if test_url:
    config.set_main_option("sqlalchemy.url", test_url)


# ==============================================================================
# Удаленный старый код с логированием
# logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG if os.getenv("DEBUG") else logging.INFO)

# def get_url():
#     cfg_url = config.get_main_option("sqlalchemy.url")
#     test_url = os.getenv("TEST_DATABASE_URL")
#     db_url = os.getenv("DATABASE_URL")

#     logger.info(
#         f"alembic.env cfg.sqlalchemy.url={cfg_url!r} TEST_DATABASE_URL={test_url!r} DATABASE_URL={db_url!r}"
#     )

#     return cfg_url or test_url or db_url
# ==============================================================================


def run_migrations_offline():
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


# ==============================================================================
# Новый метод для онлайн-миграций с синхронным подключением
def run_migrations_online():
    connectable = create_engine(get_url(), poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


# ==============================================================================
# Удаленный старый код с асинхронными миграциями
# async def run_migrations_online():
#     """
#     Запуск онлайн-миграций (асинхронное подключение к БД и применение миграций).
#     """
#     url = get_url()
#     if not url:
#         raise RuntimeError("sqlalchemy.url is not set in alembic.ini or via env")

#     logger.info(f"Online migrations with url={url}")

#     connectable = create_async_engine(url, future=True, echo=False)

#     try:
#         async with connectable.connect() as connection:
#             await connection.run_sync(do_run_migrations)
#     except Exception as e:
#         logger.error(f"Ошибка при миграции: {e}")
#         raise
# ==============================================================================

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
