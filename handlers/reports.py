# handlers/reports.py
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from models.user import User
from services.reports import get_user_report

router = Router()


@router.message(Command("reports"))
async def reports_cmd(message: Message, session: AsyncSession, user: User):
    report_data = await get_user_report(session, user)
    await message.answer(
        f"**Ваш отчёт:**\n"
        f"Завершённых задач: {report_data['completed_tasks']}\n"
        f"Задач в работе: {report_data['in_progress_tasks']}"
    )
