from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.company import Company
from models.user import User
from models.trial import Trial
from utils.enums import UserRole
from config import TRIAL_DAYS_DEFAULT

UTC = timezone.utc


async def create_company(session: AsyncSession, name: str, created_by: int) -> Company:
    """Создаёт компанию и автоматически триал в одной транзакции."""
    company = Company(name=name, created_by=created_by)
    session.add(company)
    await session.flush()  # получаем company.id

    # Стартуем триал
    trial = Trial(
        company_id=company.id,
        starts_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(days=TRIAL_DAYS_DEFAULT),
        is_active=True,
        created_by=created_by,
    )
    session.add(trial)

    # Привязываем создателя к компании
    user = await session.get(User, created_by)
    if user:
        user.company_id = company.id
        user.role = UserRole.manager  # <- владелец компании
        session.add(user)

    await session.flush()
    return company


async def get_company_by_name(session: AsyncSession, name: str) -> Company | None:
    q = await session.execute(select(Company).where(Company.name == name))
    return q.scalar_one_or_none()


async def get_company_by_id(session: AsyncSession, company_id: int) -> Company | None:
    return await session.get(Company, company_id)


async def join_company(
    session: AsyncSession,
    user: User,
    company: Company,
    role: UserRole = UserRole.worker,
) -> User:
    """Присоединяет пользователя к компании с указанной ролью (по умолчанию WORKER)."""
    user.company_id = company.id
    user.role = role
    session.add(user)
    await session.flush()
    return user
