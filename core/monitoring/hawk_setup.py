import os
import structlog
import hawkcatcher

logger = structlog.get_logger(__name__)


def setup_hawk():
    """Инициализация Hawk SDK (совместимо с hawkcatcher 3.4.1)."""
    dsn = os.getenv("HAWK_DSN")
    if not dsn:
        logger.warning("⚠️ HAWK_DSN not provided — Hawk disabled.")
        return

    try:
        # В новой версии init принимает dsn без имени аргумента
        hawkcatcher.init(dsn)
        logger.info("🦅 Hawk initialized successfully (v3.4.1 API)")
    except Exception as e:
        logger.warning(f"⚠️ Hawk initialization failed: {e}")


def capture_exception(e: Exception):
    """Отправка исключения в Hawk (новый API)."""
    try:
        hawkcatcher.send(e)
    except Exception as err:
        logger.warning(f"⚠️ Failed to send exception to Hawk: {err}")


def capture_message(msg):
    """Отправка произвольного сообщения или исключения в Hawk."""
    try:
        if isinstance(msg, BaseException):
            hawkcatcher.send(msg)
        else:
            hawkcatcher.send(Exception(str(msg)))
    except Exception as err:
        logger.warning(f"⚠️ Failed to send message to Hawk: {err}")
