# conftest.py
import os
import logging
import pytest
import pytest_asyncio

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text
from alembic.config import Config
from alembic import command
from models.base import Base
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ----------------------
# 🔹 Load environment for tests
# ----------------------
ENV_TEST_PATH = ".env.test"
if os.path.exists(ENV_TEST_PATH):
    load_dotenv(ENV_TEST_PATH, override=True)
    print(f"✅ Loaded {ENV_TEST_PATH}")
else:
    load_dotenv(".env", override=False)
    print("⚠️ .env.test not found — loaded default .env (not recommended for tests)")


# ----------------------
# 🔹 Build URLs and enforce test safety
# ----------------------
def ensure_sync_url(url: str) -> str:
    if not url:
        return ""
    return url.replace("+asyncpg", "+psycopg2") if "+asyncpg" in url else url


# Try all possible sources for DB connection
ASYNC_TEST_DATABASE_URL = (
    os.getenv("ASYNC_TEST_DATABASE_URL")
    or os.getenv("DATABASE_URL")
    or f"postgresql+asyncpg://{os.getenv('POSTGRES_USER', 'saasuser')}:{os.getenv('POSTGRES_PASSWORD', 'saaspass')}@{os.getenv('POSTGRES_HOST', 'localhost')}:{os.getenv('POSTGRES_PORT', '5432')}/{os.getenv('POSTGRES_DB', 'saasdb_test')}"
)
SYNC_TEST_DATABASE_URL = (
    os.getenv("SYNC_TEST_DATABASE_URL")
    or ensure_sync_url(ASYNC_TEST_DATABASE_URL)
)

if not ASYNC_TEST_DATABASE_URL:
    raise RuntimeError(
        "❌ ASYNC_TEST_DATABASE_URL not set — check .env.test or env_file"
    )

# Force DATABASE_URL to point to test DB
os.environ["DATABASE_URL"] = ASYNC_TEST_DATABASE_URL
os.environ["SYNC_TEST_DATABASE_URL"] = SYNC_TEST_DATABASE_URL

# Safety guard
if "test" not in (ASYNC_TEST_DATABASE_URL or ""):
    raise RuntimeError(
        f"❌ Refusing to run tests against non-test database!\nDATABASE_URL={ASYNC_TEST_DATABASE_URL}"
    )

logger.info(f"[pytest.conftest] ASYNC_TEST_DATABASE_URL={ASYNC_TEST_DATABASE_URL}")
logger.info(f"[pytest.conftest] SYNC_TEST_DATABASE_URL={SYNC_TEST_DATABASE_URL}")


# ----------------------
# 🔹 Apply migrations (once per session)
# ----------------------
@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    """Run migrations once for smoke/flow tests."""
    if os.getenv("USE_MIGRATIONS", "true").lower() != "true":
        return

    logger.info("🚀 Applying migrations...")
    sync_engine = create_engine(SYNC_TEST_DATABASE_URL)

    reset_db = os.getenv("RESET_DB", "true").lower() == "true"
    if reset_db:
        with sync_engine.begin() as conn:
            conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
            conn.execute(text("CREATE SCHEMA public"))

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", SYNC_TEST_DATABASE_URL)
    alembic_cfg.set_main_option("script_location", "migrations")
    command.upgrade(alembic_cfg, "head")
    logger.info("✅ Migrations applied")


# ----------------------
# 🔹 Async test session
# ----------------------
@pytest_asyncio.fixture(scope="function")
async def engine(apply_migrations):
    async_engine = create_async_engine(ASYNC_TEST_DATABASE_URL, echo=False, future=True)
    yield async_engine
    await async_engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def session(engine):
    async_session = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession, future=True
    )
    async with async_session() as s:
        yield s


# ----------------------
# 🔹 Sync session (for cascade/unit tests)
# ----------------------
@pytest.fixture(scope="function")
def db_session():
    sync_engine = create_engine(SYNC_TEST_DATABASE_URL)
    Session = sessionmaker(bind=sync_engine)
    session = Session()

    Base.metadata.drop_all(bind=sync_engine)
    Base.metadata.create_all(bind=sync_engine)

    try:
        yield session
    finally:
        session.rollback()
        session.close()
        sync_engine.dispose()
