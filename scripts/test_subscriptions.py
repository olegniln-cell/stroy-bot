# scripts/test_subscriptions.py
# -*- coding: utf-8 -*-
"""
Тесты для сервисов подписок и middleware-декоратора.
"""
import sys
import os
import asyncio

from sqlalchemy import select

from database import async_session_maker
from models.company import Company
from models.user import User
from services.subscriptions import (
    create_subscription,
    get_active_subscription,
    has_active_subscription_for_user,
)
from utils.subscription_check import require_subscription


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


async def main():
    async with async_session_maker() as session:
        # 1. ensure company exists
        stmt = select(Company).where(Company.id == 1)
        company = (await session.execute(stmt)).scalar_one_or_none()
        if not company:
            company = Company(id=1, name="TestCo")
            session.add(company)
            print("✅ Created test company id=1")

        # 2. ensure user exists
        user = await session.get(User, 1)
        if not user:
            user = User(id=1, tg_id=12345, role="admin")
            session.add(user)
            print("✅ Created test user id=1")

        await session.commit()

        # 3. create subscription
        try:
            sub = await create_subscription(
                session, company_id=1, plan_code="free", actor_id=1, commit=True
            )
            print(
                f"✅ Created subscription id={sub.id}, status={sub.status}, "
                f"start={sub.starts_at}, expire={sub.expires_at}"
            )
        except Exception as e:
            print("⚠️ Create failed:", e)

        # 4. get active subscription
        active = await get_active_subscription(session, 1)
        print("📊 Active subscription:", active.id if active else None)

        # 5. test has_active_subscription_for_user
        ok = await has_active_subscription_for_user(session, user_id=1)
        print("👤 User 1 has active subscription?", ok)

        # 6. test require_subscription decorator
        @require_subscription
        async def my_handler(session, user_id):
            return f"Привет, подписка есть у user_id={user_id}!"

        try:
            msg = await my_handler(session=session, user_id=1)
            print("💬 Handler result:", msg)
        except Exception as e:
            print("❌ Handler denied:", e)


if __name__ == "__main__":
    asyncio.run(main())
