import pytest
from services.users import get_or_create_user
from services.companies import create_company, join_company
from services.projects import create_project, get_projects_by_company_id
from services.tasks import create_task, get_my_tasks
from tests.utils import unique_tg_id
from utils.enums import TaskStatus
from services.tasks import set_task_status
from sqlalchemy import select
from models.audit_log import AuditLog


@pytest.mark.smoke
@pytest.mark.smoke_core
@pytest.mark.asyncio
async def test_core_flow(session):
    user, created = await get_or_create_user(session, tg_id=unique_tg_id())  # 👈
    await session.commit()
    assert created is True
    assert user.id

    company = await create_company(session, name="CoreCo", created_by=user.id)
    await session.commit()
    assert company.id

    user = await join_company(session, user, company)
    await session.commit()
    assert user.company_id == company.id

    project = await create_project(session, name="Core Project", company_id=company.id)
    assert project.id

    projects = await get_projects_by_company_id(session, company.id)
    assert any(p.id == project.id for p in projects)

    task = await create_task(
        session,
        title="Core Task",
        description="Check flow",
        project_id=project.id,
        company_id=company.id,
        user_id=user.id,
    )
    assert task.id

    my_tasks = await get_my_tasks(session, user.id)
    assert any(t.id == task.id for t in my_tasks)

    # ✅ Проверка смены статуса задачи

    task2 = await set_task_status(
        session, task.id, TaskStatus.in_progress.value, company.id
    )
    await session.commit()
    assert task2.status == TaskStatus.in_progress.value

    # ✅ Проверка, что аудит записался

    logs = (await session.execute(select(AuditLog))).scalars().all()
    assert len(logs) >= 1
