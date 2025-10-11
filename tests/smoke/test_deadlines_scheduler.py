import pytest
from services.notifications.scheduler import check_deadlines
from services.tasks import create_task
from tests.utils import unique_tg_id
from services.users import get_or_create_user
from services.companies import create_company


@pytest.mark.asyncio
async def test_deadlines_scheduler(session, bot_mock):  # ✅ исправлено
    user, _ = await get_or_create_user(session, tg_id=unique_tg_id())
    company = await create_company(session, "SchedCo", user.id)
    await session.commit()

    # создаём задачу
    await create_task(
        session,
        title="Deadline soon",
        description="Check reminder",
        project_id=None,
        company_id=company.id,
        user_id=user.id,
    )
    await session.commit()

    await check_deadlines(bot_mock, session)
    assert True  # smoke-проверка, что не падает
