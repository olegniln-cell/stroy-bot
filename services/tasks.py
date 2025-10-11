from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.task import Task
from datetime import datetime, UTC
from typing import Optional
from services.audit import log_action


async def create_task(
    session: AsyncSession,
    title: str,
    description: str,
    project_id: int,
    company_id: int,
    user_id: int,
) -> Task:
    try:
        new_task = Task(
            title=title,
            description=description,
            project_id=project_id,
            company_id=company_id,
            user_id=user_id,
            created_at=datetime.now(UTC),
        )
        session.add(new_task)
        await session.flush()
        # await session.commit()   Удаляем commit внутри service — commit должен быть в handler
        await session.refresh(new_task)  # Обновляем объект
        return new_task
    except Exception as e:
        await session.rollback()
        raise e


async def get_task_by_id_and_company(
    session: AsyncSession, task_id: int, company_id: int
) -> Optional[Task]:
    """
    Получает задачу по ID, убеждаясь, что она принадлежит нужной компании.
    """
    result = await session.execute(
        select(Task).filter(Task.id == task_id, Task.company_id == company_id)
    )
    return result.scalar_one_or_none()


async def get_my_tasks(session: AsyncSession, user_id: int) -> list[Task]:
    """
    Получает все задачи, назначенные текущему пользователю.
    """
    result = await session.execute(select(Task).where(Task.user_id == user_id))
    return result.scalars().all()


# --- ИЗМЕНЕНИЕ: reassign_task ---
# Вместо get_task_by_id (уязвимой) используем get_task_by_id_and_company (безопасную)
async def reassign_task(
    session: AsyncSession, task_id: int, new_user_id: int, company_id: int
) -> Optional[Task]:
    """
    Переназначает задачу другому пользователю, с проверкой принадлежности к компании.
    """
    task = await get_task_by_id_and_company(
        session, task_id, company_id
    )  # <- Используем новую функцию
    if task:
        task.user_id = new_user_id
        session.add(task)
    return task


# --- ИЗМЕНЕНИЕ: set_task_status ---
# То же самое: добавляем company_id и используем безопасную функцию
async def set_task_status(
    session: AsyncSession, task_id: int, status: str, company_id: int
) -> Optional[Task]:
    """
    Устанавливает статус для задачи, с проверкой принадлежности к компании.
    Также создаёт запись в аудит-логе.
    """
    task = await get_task_by_id_and_company(session, task_id, company_id)
    if not task:
        return None

    task.status = status
    session.add(task)

    # ✅ создаём запись в аудит-логе
    await log_action(
        session=session,
        actor_user_id=None,  # если знаешь user_id, можно передать его сюда
        actor_tg_id=None,  # аналогично, если доступен tg_id
        action="status_changed",
        entity_type="task",
        entity_id=task_id,
        payload={"new_status": status},
    )

    return task
