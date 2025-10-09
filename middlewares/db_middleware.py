# middlewares/db_middleware.py
from aiogram import BaseMiddleware
from typing import Callable, Dict, Any
import time
import structlog
from prometheus_client import Counter, Histogram

logger = structlog.get_logger()

DB_REQUESTS_TOTAL = Counter("db_requests_total", "Total DB session usages", ["status"])
DB_REQUEST_DURATION = Histogram(
    "db_request_duration_seconds", "DB session duration in seconds", ["status"]
)


class DbSessionMiddleware(BaseMiddleware):
    """Best-practice: чистая работа с БД + метрики, без зависимости от Hawk."""

    def __init__(self, session_pool):
        super().__init__()
        self.session_pool = session_pool

    async def __call__(self, handler: Callable, event, data: Dict[str, Any]) -> Any:
        start = time.monotonic()
        status = "ok"
        try:
            async with self.session_pool() as session:
                data["session"] = session
                result = await handler(event, data)
                return result
        except Exception:
            status = "error"
            raise
        finally:
            duration = time.monotonic() - start
            DB_REQUESTS_TOTAL.labels(status=status).inc()
            DB_REQUEST_DURATION.labels(status=status).observe(duration)
            logger.info(
                "DB session finished", duration=f"{duration:.3f}s", status=status
            )
