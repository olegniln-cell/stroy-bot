import pytest
from sqlalchemy import select
from services.users import get_or_create_user
from services.companies import create_company, join_company
from services.projects import create_project
from services.tasks import create_task, set_task_status, get_task_by_id_and_company
from models.audit_log import AuditLog
from utils.enums import TaskStatus
from tests.utils import unique_tg_id


@pytest.mark.smoke
@pytest.mark.smoke_review
@pytest.mark.asyncio
async def test_review_flow(session):
    """
    Полный цикл: создание задачи -> взятие в работу -> завершение -> проверка (approve/reject)
    """

    # 1️⃣ Создаём пользователя и компанию
    user, _ = await get_or_create_user(session, tg_id=unique_tg_id())
    await session.commit()

    company = await create_company(session, name="ReviewCo", created_by=user.id)
    await session.commit()

    user = await join_company(session, user, company)
    await session.commit()

    # 2️⃣ Создаём проект и задачу
    project = await create_project(session, "Review Project", company.id)
    task = await create_task(
        session,
        "Review Task",
        "End-to-end check",
        project.id,
        company.id,
        user.id,
    )
    await session.commit()

    # 3️⃣ Берём задачу в работу
    t1 = await set_task_status(
        session, task.id, TaskStatus.in_progress.value, company.id
    )
    await session.commit()
    assert t1.status == TaskStatus.in_progress.value

    # 4️⃣ Завершаем задачу
    t2 = await set_task_status(session, task.id, TaskStatus.ready.value, company.id)
    await session.commit()
    assert t2.status == TaskStatus.ready.value

    # 5️⃣ Проверяем (approve)
    t3 = await set_task_status(session, task.id, TaskStatus.approved.value, company.id)
    await session.commit()
    assert t3.status == TaskStatus.approved.value

    # 6️⃣ Проверяем (reject)
    t4 = await set_task_status(session, task.id, TaskStatus.rework.value, company.id)
    await session.commit()
    assert t4.status == TaskStatus.rework.value

    # 7️⃣ Проверяем, что аудит пишет события
    logs = (await session.execute(select(AuditLog))).scalars().all()
    actions = [log.action for log in logs]
    assert any(a in actions for a in ["status_changed", "approve_task", "reject_task"])

    # 8️⃣ Проверяем, что задача в базе в ожидаемом статусе
    latest = await get_task_by_id_and_company(session, task.id, company.id)
    assert latest.status == TaskStatus.rework.value
