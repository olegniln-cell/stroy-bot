# services/users.py
import logging
from datetime import datetime, UTC
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.user import User
from utils.enums import UserRole

logger = logging.getLogger(__name__)


async def get_or_create_user(session: AsyncSession, tg_id: int):
    q = select(User).where(User.tg_id == tg_id)
    res = await session.execute(q)
    user = res.scalar_one_or_none()
    if user:
        return user, False

    user = User(
        tg_id=tg_id,
        role=UserRole.client,  # ✅ любое из существующих
        company_id=None,
        phone_number=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    session.add(user)
    await session.flush()  # получаем ID
    return user, True


async def get_user_by_tg_id(session: AsyncSession, tg_id: int):
    result = await session.execute(select(User).filter(User.tg_id == tg_id))
    return result.scalar_one_or_none()


async def set_user_role_and_company(
    session: AsyncSession, user_id: int, role: UserRole, company_id: int = None
):
    logger.debug(f"Устанавливаем роль {role.name} для пользователя {user_id}")

    if not isinstance(role, UserRole):
        raise ValueError("Неверный тип роли")

    user = await session.get(User, user_id)
    if not user:
        raise ValueError("Пользователь не найден")

    if company_id in ("", None):
        user.company_id = None
    else:
        user.company_id = int(company_id)

    user.role = role
    await session.flush()
    return user
