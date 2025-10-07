import os
from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from models.base import Base

# Читаем атомарные ENV (с дефолтами для локала)
POSTGRES_USER = os.getenv("POSTGRES_USER", "saasuser")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "saaspass")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "saasdb")

# Сборка полного URL
DATABASE_URL = (
    os.getenv("DATABASE_URL")
    or os.getenv("TEST_DATABASE_URL")
    or f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

# Async engine + sessionmaker
async_engine = create_async_engine(DATABASE_URL, echo=False, future=True)
async_session_maker = async_sessionmaker(
    bind=async_engine, class_=AsyncSession, expire_on_commit=False
)


async def init_db():
    """Создание всех таблиц (без сидирования тарифов)."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return async_session_maker


# Audit поля
def set_audit_fields(session, flush_context, instances):
    actor_id = session.info.get("actor_id")
    if not actor_id:
        return
    for obj in session.new:
        if hasattr(obj, "created_by") and not getattr(obj, "created_by", None):
            obj.created_by = actor_id
    for obj in session.dirty:
        if hasattr(obj, "updated_by"):
            obj.updated_by = actor_id


event.listen(async_session_maker().sync_session_class, "before_flush", set_audit_fields)
