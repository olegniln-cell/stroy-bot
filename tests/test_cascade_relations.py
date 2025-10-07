import pytest
from sqlalchemy import select
from models import Company, Project, Task, File


@pytest.mark.asyncio
async def test_delete_project_cascades_tasks_and_files(db_session):
    """Удаление проекта должно каскадно удалять связанные задачи и файлы."""

    # 1️⃣ Создаём компанию
    company = Company(name="Test Company")
    db_session.add(company)
    db_session.flush()  # без await, потому что sync session

    # 2️⃣ Создаём проект, задачу и файл
    project = Project(name="Demo project", company_id=company.id)
    task = Task(title="Test task", company_id=company.id, project=project)
    file = File(
        task=task,
        company_id=company.id,
        s3_key="demo/file.txt",
        original_name="file.txt",
        size=100,
        mime_type="text/plain",
    )

    db_session.add_all([project, task, file])
    db_session.commit()

    # 3️⃣ Удаляем проект
    db_session.delete(project)
    db_session.commit()

    # 4️⃣ Проверяем каскад
    assert not db_session.scalar(select(Task).where(Task.project_id == project.id))
    assert not db_session.scalar(select(File).where(File.task_id == task.id))
