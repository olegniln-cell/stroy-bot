# scripts/seed.py
# -*- coding: utf-8 -*-
"""
Идемпотентный посев: создает тарифные планы (free/basic/pro) и администратора (id=1).
Надежные импорты: пытается найти фабрику асинхронной сессии в нескольких модулях.
"""
import sys
import os
import asyncio
import traceback
from typing import Tuple
from utils.enums import UserRole

from sqlalchemy import select

# --- убедиться, что корневая директория проекта в sys.path ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


# --- вспомогательная функция: поиск фабрики асинхронной сессии ---
def find_session_factory() -> Tuple[callable, str]:
    candidates = [
        ("app.db.session", "async_session_maker"),
        ("app.db.session", "async_session"),
        ("db.session", "async_session_maker"),
        ("db.session", "async_session"),
        ("database", "async_session_maker"),
        ("database", "async_session"),
        ("app.database", "async_session_maker"),
    ]
    for mod_name, attr in candidates:
        try:
            mod = __import__(mod_name, fromlist=[attr])
            if hasattr(mod, attr):
                return getattr(mod, attr), f"{mod_name}.{attr}"
        except Exception:
            continue
    raise RuntimeError(
        "Не удалось найти фабрику асинхронной сессии. Поиски велись в: "
        + ", ".join(f"{m}.{a}" for m, a in candidates)
    )


# --- импорт моделей (пытается из нескольких путей) ---
try:
    from models.plan import Plan
    from models.user import User
except Exception:
    try:
        from app.models.plan import Plan
        from app.models.user import User
    except Exception as e:
        raise RuntimeError("Не удалось импортировать модели Plan/User: " + str(e))

# --- конфигурация данных для посева ---
PLANS = [
    {
        "code": "free",
        "name": "Бесплатный тариф",
        "monthly_price": 0,
        "period_days": 14,
        "features": {"features": ["базовые"]},
    },
    {
        "code": "basic",
        "name": "Базовый тариф",
        "monthly_price": 10,
        "period_days": 30,
        "features": {"features": ["задачи", "файлы"]},
    },
    {
        "code": "pro",
        "name": "Профессиональный тариф",
        "monthly_price": 30,
        "period_days": 30,
        "features": {"features": ["задачи", "файлы", "аналитика"]},
    },
]

ADMIN = {"id": 1, "tg_id": 0, "role": UserRole.admin}


# --- основная процедура посева ---
async def seed():
    session_factory, found = find_session_factory()
    print("Используется фабрика сессий:", found)
    try:
        async with session_factory() as session:
            # Тарифные планы
            added = 0
            for p in PLANS:
                stmt = select(Plan).where(Plan.code == p["code"])
                res = await session.execute(stmt)
                exists = res.scalar_one_or_none()
                if exists:
                    print(f"⚪ План уже существует: {p['code']}")
                else:
                    plan_payload = {
                        "code": p["code"],
                        "name": p["name"],
                        "monthly_price": p["monthly_price"],
                        "period_days": p["period_days"],
                        "features": p.get("features", None),
                    }
                    session.add(Plan(**plan_payload))
                    print(f"✅ Добавлен план: {p['code']}")
                    added += 1

            # Администратор по id
            admin_obj = await session.get(User, ADMIN["id"])
            if admin_obj:
                print("⚪ Администратор уже существует (id=1)")
            else:
                # create minimal required fields; model may require other fields — adjust if needed
                admin_payload = {
                    "id": ADMIN["id"],
                    "tg_id": ADMIN["tg_id"],
                    "role": ADMIN["role"],
                }
                session.add(User(**admin_payload))
                print("✅ Добавлен администратор (id=1)")

            await session.commit()
            print(f"\nПосев закончен. Добавлены планы: {added}")
    except Exception as e:
        print("ERROR во время посева():", e)
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(seed())
