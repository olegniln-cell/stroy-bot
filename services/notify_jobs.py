from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram import Bot
from models import Trial, Subscription, User
from utils.enums import UserRole, SubscriptionStatus
from config import BILLING_REMIND_DAYS

import logging

UTC = timezone.utc
logger = logging.getLogger(__name__)


async def _company_admins_and_managers(session: AsyncSession, company_id: int):
    """Получаем всех админов и менеджеров компании"""
    q = await session.execute(
        select(User).where(
            User.company_id == company_id,
            User.role.in_([UserRole.ADMIN.value, UserRole.MANAGER.value]),
        )
    )
    return q.scalars().all()


async def notify_expiring_trials(session: AsyncSession, bot: Bot):
    """Уведомления о том, что триал скоро закончится"""
    now = datetime.now(UTC)
    target = now + timedelta(days=BILLING_REMIND_DAYS)

    q = await session.execute(
        select(Trial).where(Trial.is_active, Trial.expires_at.between(now, target))
    )

    for trial in q.scalars().all():
        managers = await _company_admins_and_managers(session, trial.company_id)
        for u in managers:
            try:
                await bot.send_message(
                    u.tg_id,
                    f"⚠️ У компании #{trial.company_id} триал заканчивается {trial.expires_at:%Y-%m-%d}. "
                    f"Продлите или оформите подписку.",
                )
            except Exception as e:
                logger.warning(
                    f"Не удалось отправить сообщение пользователю {u.tg_id}: {e}"
                )


async def notify_expiring_subscriptions(session: AsyncSession, bot: Bot):
    """Уведомления о том, что подписка скоро закончится"""
    now = datetime.now(UTC)
    target = now + timedelta(days=BILLING_REMIND_DAYS)

    q = await session.execute(
        select(Subscription).where(
            Subscription.status == SubscriptionStatus.active.value,
            Subscription.expires_at.between(now, target),
        )
    )

    for sub in q.scalars().all():
        managers = await _company_admins_and_managers(session, sub.company_id)
        for u in managers:
            try:
                await bot.send_message(
                    u.tg_id,
                    f"⚠️ Подписка компании #{sub.company_id} истекает {sub.expires_at:%Y-%m-%d}. "
                    f"Оплатите, чтобы избежать блокировки.",
                )
            except Exception as e:
                logger.warning(
                    f"Не удалось отправить сообщение пользователю {u.tg_id}: {e}"
                )


async def enforce_expirations(session: AsyncSession, bot: Bot):
    """В день окончания: отключаем триал и подписку"""
    now = datetime.now(UTC)

    # триалы
    q_t = await session.execute(
        select(Trial).where(Trial.is_active, Trial.expires_at <= now)
    )
    for t in q_t.scalars().all():
        t.is_active = False
        managers = await _company_admins_and_managers(session, t.company_id)
        for u in managers:
            try:
                await bot.send_message(
                    u.tg_id,
                    f"⛔ Триал компании #{t.company_id} завершён. Доступ ограничен.",
                )
            except Exception as e:
                logger.warning(
                    f"Не удалось отправить сообщение пользователю {u.tg_id}: {e}"
                )

    # подписки
    q_s = await session.execute(
        select(Subscription).where(
            Subscription.status == SubscriptionStatus.active.value,
            Subscription.expires_at <= now,
        )
    )
    for s in q_s.scalars().all():
        s.status = SubscriptionStatus.expired.value
        managers = await _company_admins_and_managers(session, s.company_id)
        for u in managers:
            try:
                await bot.send_message(
                    u.tg_id,
                    f"⛔ Подписка компании #{s.company_id} истекла. Доступ ограничен.",
                )
            except Exception as e:
                logger.warning(
                    f"Не удалось отправить сообщение пользователю {u.tg_id}: {e}"
                )


async def run_all(session: AsyncSession, bot: Bot):
    """Запуск всех задач подряд"""
    await notify_expiring_trials(session, bot)
    await notify_expiring_subscriptions(session, bot)
    await enforce_expirations(session, bot)
