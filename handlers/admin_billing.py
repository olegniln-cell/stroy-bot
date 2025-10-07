# handlers/admin_billing.py
from aiogram import Router, types, F
from sqlalchemy.ext.asyncio import AsyncSession
from utils.enums import UserRole
from services.subscriptions import (
    extend_trial,
    set_plan_for_company,
    pause_subscription,
    resume_subscription,
    cancel_subscription,
    get_company_subscription_status,
)

router = Router(name="admin_billing")


def _is_admin(user) -> bool:
    return getattr(user, "role", None) == UserRole.admin.value


def fmt_date(dt):
    return dt.strftime("%Y-%m-%d") if dt else "—"


@router.message(F.text.regexp(r"^/admin_extend_trial\s+\d+\s+\d+$"))
async def cmd_extend_trial(message: types.Message, session: AsyncSession, user):
    if not _is_admin(user):
        await message.answer("Недостаточно прав.")
        return
    _, company_id, extra_days = message.text.split()
    company_id = int(company_id)
    extra_days = int(extra_days)

    trial = await extend_trial(session, company_id, extra_days)
    await message.answer(
        f"✅ Триал для компании {company_id} продлён. "
        f"Новая дата окончания: {trial.expires_at:%Y-%m-%d}."
    )


@router.message(F.text.regexp(r"^/admin_set_plan\s+\d+\s+\w+(\s+\d+)?$"))
async def cmd_set_plan(message: types.Message, session: AsyncSession, user):
    if not _is_admin(user):
        await message.answer("Недостаточно прав.")
        return
    parts = message.text.split()
    # /admin_set_plan <company_id> <plan_code> [months]
    company_id = int(parts[1])
    plan_code = parts[2]
    months = int(parts[3]) if len(parts) > 3 else 1

    sub = await set_plan_for_company(session, company_id, plan_code, months)
    await message.answer(
        f"✅ Для компании {company_id} установлен план '{plan_code}'. "
        f"Действует до {sub.expires_at:%Y-%m-%d}."
    )


@router.message(F.text.regexp(r"^/admin_pause\s+\d+$"))
async def cmd_pause(message: types.Message, session: AsyncSession, user):
    if not _is_admin(user):
        await message.answer("Недостаточно прав.")
        return
    company_id = int(message.text.split()[1])
    ok = await pause_subscription(session, company_id)
    await message.answer(
        "✅ Подписка поставлена на паузу." if ok else "ℹ️ Подписка не найдена."
    )


@router.message(F.text.regexp(r"^/admin_resume\s+\d+$"))
async def cmd_resume(message: types.Message, session: AsyncSession, user):
    if not _is_admin(user):
        await message.answer("Недостаточно прав.")
        return
    company_id = int(message.text.split()[1])
    ok = await resume_subscription(session, company_id)
    await message.answer(
        "✅ Подписка возобновлена." if ok else "ℹ️ Подписка не найдена."
    )


@router.message(F.text.regexp(r"^/admin_cancel\s+\d+$"))
async def cmd_cancel(message: types.Message, session: AsyncSession, user):
    if not _is_admin(user):
        await message.answer("Недостаточно прав.")
        return
    company_id = int(message.text.split()[1])
    ok = await cancel_subscription(session, company_id)
    await message.answer("✅ Подписка отменена." if ok else "ℹ️ Подписка не найдена.")


@router.message(F.text.regexp(r"^/admin_company_status\s+\d+$"))
async def cmd_company_status(message: types.Message, session: AsyncSession, user):
    if not _is_admin(user):
        await message.answer("Недостаточно прав.")
        return
    company_id = int(message.text.split()[1])
    st = await get_company_subscription_status(session, company_id)
    trial, sub = st["trial"], st["subscription"]

    trial_info = "—"
    if trial["exists"]:
        trial_info = f"{fmt_date(trial['starts_at'])} → {fmt_date(trial['expires_at'])}"

    sub_info = "—"
    if sub["exists"]:
        sub_info = f"{sub['status']} ({fmt_date(sub['starts_at'])} → {fmt_date(sub['expires_at'])})"

    txt = [
        f"🏢 Компания {company_id}",
        f"Доступ: {'доступен' if st['available'] else 'заблокирован'}",
        f"Trial: {'активен' if trial.get('is_active') else 'нет'} ({trial_info})",
        f"Подписка: {sub.get('status') or 'нет'} ({sub_info})",
    ]
    await message.answer("\n".join(txt))
