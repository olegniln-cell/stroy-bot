import pytest
from sqlalchemy import select
from models import Trial
from services.users import get_or_create_user
from services.companies import create_company
from services.subscriptions import has_active_subscription_for_user
from tests.utils import unique_tg_id


@pytest.mark.smoke
@pytest.mark.smoke_billing
@pytest.mark.asyncio
async def test_billing_flow(session):
    user, _ = await get_or_create_user(session, tg_id=unique_tg_id())  # 👈 используем
    await session.commit()

    company = await create_company(session, name="BillingCo", created_by=user.id)
    await session.commit()

    trial_q = await session.execute(select(Trial).where(Trial.company_id == company.id))
    trial = trial_q.scalar_one()
    assert trial.is_active is True

    has_sub = await has_active_subscription_for_user(session, user.id)
    assert has_sub is True
