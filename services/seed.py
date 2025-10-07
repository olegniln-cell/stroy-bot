# services/seed.py
# -*- coding: utf-8 -*-
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from models.plan import Plan

logger = logging.getLogger(__name__)

DEFAULT_PLANS = [
    {
        "code": "free",
        "name": "Free",
        "monthly_price": 0,
        "period_days": 30,
        "features": {},
    },
    {
        "code": "pro",
        "name": "Pro",
        "monthly_price": 29,
        "period_days": 30,
        "features": {},
    },
    {
        "code": "enterprise",
        "name": "Enterprise",
        "monthly_price": 199,
        "period_days": 365,
        "features": {},
    },
]


async def seed_plans(session: AsyncSession) -> None:
    """
    UPSERT тарифов: обновляет поля, если тариф уже существует.
    """
    for plan in DEFAULT_PLANS:
        stmt = insert(Plan).values(**plan)
        update_fields = {
            "name": stmt.excluded.name,
            "monthly_price": stmt.excluded.monthly_price,
            "period_days": stmt.excluded.period_days,
        }
        # если колонка features есть в модели, добавляем в UPSERT
        if hasattr(Plan, "features"):
            update_fields["features"] = stmt.excluded.features

        stmt = stmt.on_conflict_do_update(
            index_elements=["code"],
            set_=update_fields,
        )
        await session.execute(stmt)

        logger.info(
            "🔄 Тариф синхронизирован: %s | %s | %s$/мес | %s дней",
            plan["code"],
            plan["name"],
            plan["monthly_price"],
            plan["period_days"],
        )

    await session.commit()
    logger.info("✅ Синхронизация тарифов завершена (созданы/обновлены)")
