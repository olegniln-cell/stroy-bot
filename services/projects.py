from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.project import Project


async def create_project(session: AsyncSession, name: str, company_id: int) -> Project:
    try:
        new_project = Project(name=name, company_id=company_id)
        session.add(new_project)
        await session.flush()
        await session.commit()  # Добавлен коммит
        await session.refresh(new_project)  # Добавлено обновление объекта
        return new_project
    except Exception as e:
        await session.rollback()  # Добавлен откат при ошибке
        raise e


async def get_projects_by_company_id(
    session: AsyncSession, company_id: int
) -> list[Project]:
    """
    Получает все проекты для указанной компании.
    """
    result = await session.execute(
        select(Project).filter(Project.company_id == company_id)
    )
    return result.scalars().all()


async def get_project_by_id_and_company(
    session: AsyncSession, project_id: int, company_id: int
) -> Project | None:
    """
    Получает проект по его ID, убеждаясь, что он принадлежит нужной компании.
    """
    result = await session.execute(
        select(Project).filter(
            Project.id == project_id, Project.company_id == company_id
        )
    )
    return result.scalar_one_or_none()
