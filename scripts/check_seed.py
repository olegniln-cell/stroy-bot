# scripts/check_seed.py
# -*- coding: utf-8 -*-
"""
Check that seed objects exist and print summary.
"""
import sys
import os
import asyncio
import traceback

from sqlalchemy import select

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


def find_session_factory():
    candidates = [
        ("app.db.session", "async_session_maker"),
        ("app.db.session", "async_session"),
        ("db.session", "async_session_maker"),
        ("db.session", "async_session"),
        ("database", "async_session_maker"),
        ("database", "async_session"),
    ]
    for mod_name, attr in candidates:
        try:
            mod = __import__(mod_name, fromlist=[attr])
            if hasattr(mod, attr):
                return getattr(mod, attr), f"{mod_name}.{attr}"
        except Exception:
            continue
    raise RuntimeError(
        "Cannot find async session factory. Tried: "
        + ", ".join(f"{m}.{a}" for m, a in candidates)
    )


try:
    from models.plan import Plan
    from models.user import User
except Exception:
    try:
        from app.models.plan import Plan
        from app.models.user import User
    except Exception as e:
        raise RuntimeError("Cannot import models: " + str(e))


async def check():
    session_factory, found = find_session_factory()
    print("Using session factory:", found)
    try:
        async with session_factory() as session:
            # plans
            res = await session.execute(select(Plan))
            plans = res.scalars().all()
            print("\n📊 Plans in DB:")
            if not plans:
                print("  (no plans)")
            for p in plans:
                # safe printing — some attributes may be None
                print(
                    f" - {getattr(p, 'code', '?')} ({getattr(p, 'name', '?')}), "
                    f"price={getattr(p, 'monthly_price', '?')}, "
                    f"period={getattr(p, 'period_days', '?')}d"
                )

            # admin by id
            admin = await session.get(User, 1)
            if admin:
                print(
                    f"\n👑 Admin found: id={admin.id}, tg_id={admin.tg_id}, role={admin.role}"
                )
            else:
                print("\n❌ Admin not found (id=1).")
    except Exception as e:
        print("ERROR during check():", e)
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(check())
