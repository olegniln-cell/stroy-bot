import pytest
from sqlalchemy import text

from models import AuditLog
from services.audit import log_action


@pytest.mark.asyncio
async def test_audit_log_insert(session):
    # очистка таблицы
    await session.execute(text("TRUNCATE TABLE audit_logs RESTART IDENTITY CASCADE"))
    await session.commit()

    # логируем действие
    await log_action(
        session=session,
        actor_user_id=1,
        actor_tg_id=111111111,
        action="test_action",
        entity_type="project",
        entity_id=123,
        payload={"info": "hello world"},
    )
    await session.commit()

    result = await session.execute(
        AuditLog.__table__.select().order_by(AuditLog.id.desc()).limit(1)
    )
    last = result.fetchone()
    assert last is not None, "❌ Запись не сохранилась!"
    assert last.action == "test_action"
