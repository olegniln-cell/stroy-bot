import logging
from models.audit_log import AuditLog

# Настройка базового логирования
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Создаём локальный логгер
logger = logging.getLogger(__name__)


async def log_action(
    session,
    actor_user_id,
    actor_tg_id,
    action,
    entity_type=None,
    entity_id=None,
    payload=None,
):
    if not action:
        raise ValueError("Действие (action) не может быть пустым")

    try:
        log = AuditLog(
            actor_user_id=actor_user_id,
            actor_tg_id=actor_tg_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=payload,
        )
        session.add(log)
        await session.flush()
        logger.info(
            f"Успешно записано действие: {action} для пользователя {actor_user_id}"
        )
    except Exception as e:
        logger.error(f"Ошибка при логировании: {str(e)}")
        raise
