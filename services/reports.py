# services/reports.py
from sqlalchemy.ext.asyncio import AsyncSession
from models.user import User


async def get_user_report(session: AsyncSession, user: User) -> dict:
    # Здесь в будущем будет логика для сбора данных по отчетам
    return {"completed_tasks": 0, "in_progress_tasks": 0}
