from aiogram import Router, types
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from utils.decorators import require_active_subscription

router = Router(name="important_stuff")


@router.message(Command("important"))
@require_active_subscription()
async def cmd_important(message: types.Message, session: AsyncSession, **kwargs):
    await message.answer("✅ Доступно только с активной подпиской")
