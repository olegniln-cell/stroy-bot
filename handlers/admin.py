# handlers/admin.py
import logging
import json
from aiogram import Router, types
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from utils.enums import UserRole
from models.audit_log import AuditLog
from aiogram.filters import Command

router = Router(name="admin")
logger = logging.getLogger(__name__)


# Изменен декоратор на Command
@router.message(Command("list_companies"))
async def list_companies_cmd(message: types.Message, session: AsyncSession, user):
    if user.role != UserRole.admin.value:
        await message.answer("⛔ Команда доступна только администраторам.")
        return

    await message.answer("⚠️ Команда /list_companies в разработке.")


# Изменен декоратор на Command
@router.message(Command("force_plan"))
async def force_plan_cmd(message: types.Message, session: AsyncSession, user):
    if user.role != UserRole.admin.value:
        await message.answer("⛔ Команда доступна только администраторам.")
        return

    await message.answer("⚠️ Команда /force_plan в разработке.")


# Изменен декоратор на Command
@router.message(Command("audit_last"))
async def audit_last_cmd(message: types.Message, session: AsyncSession, user):
    if user.role != UserRole.admin.value:
        await message.answer("⛔ Команда доступна только администраторам.")
        return

    result = await session.execute(
        select(AuditLog).order_by(AuditLog.id.desc()).limit(5)
    )
    rows = result.scalars().all()

    if not rows:
        await message.answer("📭 Логи пусты")
        return

    text = "📋 <b>Последние 5 записей audit_log:</b>\n\n"

    for row in rows:
        try:
            payload_str = json.dumps(row.payload, indent=2, ensure_ascii=False)
        except Exception:
            payload_str = str(row.payload)

        if len(payload_str) > 300:
            payload_str = payload_str[:300] + "…"

        text += (
            f"<b>ID:</b> {row.id}\n"
            f"<b>UserID:</b> {row.actor_user_id}, <b>TG:</b> {row.actor_tg_id}\n"
            f"<b>Action:</b> {row.action}\n"
            f"<b>Entity:</b> {row.entity_type}({row.entity_id})\n"
            f"<b>Payload:</b>\n<pre>{payload_str}</pre>\n"
            f"<b>Time:</b> {row.created_at}\n"
            "──────────────\n"
        )

    await message.answer(text, parse_mode="HTML")
