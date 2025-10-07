# services/payments.py
from datetime import timezone
from sqlalchemy.ext.asyncio import AsyncSession
from services.subscriptions import start_paid_subscription

UTC = timezone.utc


async def create_payment_link(company_id: int, plan_code: str, months: int = 1) -> str:
    """
    Возвращает ссылку на оплату (пока фейковая).
    В будущем тут интеграция с YooKassa или Tinkoff.
    """
    return f"https://fake-payments.local/pay?company={company_id}&plan={plan_code}&months={months}"


async def handle_payment_webhook(
    session: AsyncSession, company_id: int, plan_code: str, months: int = 1
):
    """
    Заглушка под вебхук от YooKassa/Tinkoff.
    Когда платёж подтверждён — активируем подписку.
    """
    sub = await start_paid_subscription(session, company_id, plan_code, months)
    return sub


# Позже сюда легко прикрутить yookassa SDK или API Tinkoff.
