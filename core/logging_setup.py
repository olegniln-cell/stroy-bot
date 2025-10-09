# saas_bot/core/logging_setup.py

import sys
import logging
import structlog
from core.context import request_id, user_id, company_id


def add_context(logger, method_name, event_dict):
    """
    Добавляет контекстные поля из ContextVar'ов в каждый лог.
    Вызывается structlog'ом как процессор.
    """
    event_dict["request_id"] = request_id.get()
    event_dict["user_id"] = user_id.get()
    event_dict["company_id"] = company_id.get()
    return event_dict


def setup_logging(level: int = logging.INFO):
    """
    Конфигурируем stdlib logging -> structlog.
    Вызови setup_logging() очень рано при старте приложения.
    """
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=level)

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            add_context,  # <-- наш контекстный процессор
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(level),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None):
    """Удобный accessor — вызывай после setup_logging()."""
    return structlog.get_logger(name)
