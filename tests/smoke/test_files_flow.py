import pytest
import uuid
from services.users import get_or_create_user
from services.companies import create_company, join_company
from services.projects import create_project
from services.tasks import create_task
from services.files import create_file, get_file_by_id
from tests.utils import unique_tg_id


@pytest.mark.smoke
@pytest.mark.smoke_files
@pytest.mark.asyncio
async def test_files_flow(session):
    user, _ = await get_or_create_user(session, tg_id=unique_tg_id())  # 👈
    await session.commit()

    company = await create_company(session, name="FilesCo", created_by=user.id)
    await session.commit()

    user = await join_company(session, user, company)
    await session.commit()

    project = await create_project(session, "Files Project", company.id)
    task = await create_task(
        session, "Files Task", "check files", project.id, company.id, user.id
    )
    await session.commit()

    fake_file_id = str(uuid.uuid4())
    file = await create_file(
        session,
        task_id=task.id,
        company_id=company.id,
        uploader_id=user.id,
        original_name="test.txt",
        mime_type="text/plain",
        size=123,
        s3_key=f"fake/{fake_file_id}.txt",
    )
    await session.commit()

    f2 = await get_file_by_id(session, file.id)
    assert f2 is not None
    assert f2.original_name == "test.txt"
