# services/subscription.py
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from utils.enums import SubscriptionStatus
from config import TRIAL_DAYS_DEFAULT
from models import Trial, Subscription, Plan, User


logger = logging.getLogger(__name__)

UTC = timezone.utc


class PermissionDenied(Exception):
    """Ошибка доступа при отсутствии подписки."""


# ---------- Trial ----------


async def _start_trial(
    session: AsyncSession,
    company_id: int,
    created_by: int | None = None,
    days: int = TRIAL_DAYS_DEFAULT,
) -> Trial:
    """Внутренний хелпер для создания trial (используется в extend_trial)."""
    now = datetime.now(UTC)
    trial = Trial(
        company_id=company_id,
        starts_at=now,
        expires_at=now + timedelta(days=days),
        is_active=True,
        created_by=created_by,
    )
    session.add(trial)
    await session.flush()
    return trial


async def is_trial_active(session: AsyncSession, company_id: int) -> bool:
    q = await session.execute(select(Trial).where(Trial.company_id == company_id))
    t = q.scalar_one_or_none()
    if not t:
        return False
    return t.is_active and t.expires_at > datetime.now(UTC)


async def extend_trial(
    session: AsyncSession, company_id: int, extra_days: int
) -> Trial:
    q = await session.execute(select(Trial).where(Trial.company_id == company_id))
    trial = q.scalar_one_or_none()
    now = datetime.now(UTC)

    if not trial:
        # если нет — стартуем новый на extra_days
        trial = await _start_trial(
            session, company_id, days=extra_days or TRIAL_DAYS_DEFAULT
        )
    else:
        base = trial.expires_at if trial.expires_at and trial.expires_at > now else now
        trial.expires_at = base + timedelta(days=extra_days)
        trial.is_active = True
        await session.flush()
    return trial


# ---------- Subscriptions ----------


async def _get_plan(session: AsyncSession, plan_code: str) -> Plan | None:
    q = await session.execute(select(Plan).where(Plan.code == plan_code))
    return q.scalar_one_or_none()


async def start_paid_subscription(
    session: AsyncSession, company_id: int, plan_code: str, months: int = 1
) -> Subscription:
    """Активирует платную подписку (без интеграции с платежкой)."""
    plan = await _get_plan(session, plan_code)
    if not plan:
        raise ValueError(f"Plan '{plan_code}' not found")

    now = datetime.now(UTC)
    expires = now + timedelta(days=30 * months)

    sub = Subscription(
        company_id=company_id,
        plan_id=plan.id,
        status=SubscriptionStatus.active.value,
        starts_at=now,
        expires_at=expires,
    )
    session.add(sub)

    # Триал выключаем, если был
    q = await session.execute(select(Trial).where(Trial.company_id == company_id))
    t = q.scalar_one_or_none()
    if t and t.is_active:
        t.is_active = False

    await session.flush()
    logger.info(
        "Подписка: company_id=%s, plan=%s, months=%s, expires_at=%s",
        company_id,
        plan_code,
        months,
        sub.expires_at,
    )
    return sub


async def pause_subscription(session: AsyncSession, company_id: int) -> bool:
    q = await session.execute(
        select(Subscription)
        .where(Subscription.company_id == company_id)
        .order_by(Subscription.expires_at.desc())
    )
    sub = q.scalars().first()
    if not sub:
        return False
    sub.status = SubscriptionStatus.paused.value
    await session.flush()
    return True


async def resume_subscription(session: AsyncSession, company_id: int) -> bool:
    q = await session.execute(
        select(Subscription)
        .where(Subscription.company_id == company_id)
        .order_by(Subscription.expires_at.desc())
    )
    sub = q.scalars().first()
    if not sub:
        return False
    sub.status = SubscriptionStatus.active.value
    await session.flush()
    return True


async def cancel_subscription(session: AsyncSession, company_id: int) -> bool:
    q = await session.execute(
        select(Subscription)
        .where(Subscription.company_id == company_id)
        .order_by(Subscription.expires_at.desc())
    )
    sub = q.scalars().first()
    if not sub:
        return False
    sub.status = SubscriptionStatus.canceled.value
    await session.flush()
    return True


async def mark_expired_if_needed(session: AsyncSession, company_id: int) -> bool:
    """Если активная подписка просрочена — ставим expired."""
    q = await session.execute(
        select(Subscription)
        .where(Subscription.company_id == company_id)
        .order_by(Subscription.expires_at.desc())
    )
    sub = q.scalars().first()
    if not sub:
        return False
    now = datetime.now(UTC)
    if sub.status == SubscriptionStatus.active.value and sub.expires_at <= now:
        sub.status = SubscriptionStatus.expired.value
        await session.flush()
        return True
    return False


async def has_active_subscription_for_user(session: AsyncSession, user_id: int) -> bool:
    """
    Проверяет, есть ли у пользователя активная подписка (trial или платная).
    """
    # Находим компанию пользователя
    q_user = await session.execute(select(User).where(User.id == user_id))
    user = q_user.scalar_one_or_none()
    if not user or not user.company_id:
        return False

    company_id = user.company_id

    # Проверяем trial
    q_trial = await session.execute(select(Trial).where(Trial.company_id == company_id))
    trial = q_trial.scalar_one_or_none()
    if trial and trial.is_active and trial.expires_at > datetime.now(UTC):
        return True

    # Проверяем подписку
    q_sub = await session.execute(
        select(Subscription)
        .where(Subscription.company_id == company_id)
        .order_by(Subscription.expires_at.desc())
    )
    sub = q_sub.scalars().first()
    if (
        sub
        and sub.status == SubscriptionStatus.active.value
        and sub.expires_at > datetime.now(UTC)
    ):
        return True

    return False


# ---------- Helpers ----------


async def set_plan_for_company(
    session: AsyncSession, company_id: int, plan_code: str, months: int = 1
) -> Subscription:
    """Админский хелпер без платежей — просто выдать платный период."""
    return await start_paid_subscription(
        session, company_id, plan_code=plan_code, months=months
    )


async def get_company_subscription_status(
    session: AsyncSession, company_id: int
) -> dict:
    """Сводный статус доступа: trial/subscription/available."""
    # trial
    q_t = await session.execute(select(Trial).where(Trial.company_id == company_id))
    t = q_t.scalar_one_or_none()

    # last subscription
    q_s = await session.execute(
        select(Subscription)
        .where(Subscription.company_id == company_id)
        .order_by(Subscription.expires_at.desc())
    )
    s = q_s.scalars().first()

    trial_active = bool(t and t.is_active and t.expires_at > datetime.now(UTC))
    sub_active = bool(
        s
        and s.status == SubscriptionStatus.active.value
        and s.expires_at > datetime.now(UTC)
    )

    return {
        "available": trial_active or sub_active,
        "trial": {
            "exists": bool(t),
            "is_active": trial_active,
            "starts_at": getattr(t, "starts_at", None),
            "expires_at": getattr(t, "expires_at", None),
        },
        "subscription": {
            "exists": bool(s),
            "status": getattr(s, "status", None),
            "starts_at": getattr(s, "starts_at", None),
            "expires_at": getattr(s, "expires_at", None),
            "plan_id": getattr(s, "plan_id", None),
        },
    }


# Алиас для обратной совместимости
async def create_subscription(
    session, company_id, plan_code, actor_id=None, commit=True
):
    """
    Старый алиас для set_plan_for_company, оставлен для обратной совместимости.
    Поддерживает actor_id и commit, хотя set_plan_for_company их не принимает.
    """
    sub = await set_plan_for_company(
        session=session,
        company_id=company_id,
        plan_code=plan_code,
        months=1,  # можно расширить, если нужно
    )
    if commit:
        await session.commit()
    return sub


async def get_active_subscription(session, company_id):
    """Возвращает активную подписку компании (или None)."""
    status = await get_company_subscription_status(session, company_id)
    if (
        status["subscription"]["exists"]
        and status["subscription"]["status"] == "active"
    ):
        return status["subscription"]
    return None
