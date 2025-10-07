from aiogram import Router, types
from aiogram.filters import Command
from services.payments import create_payment_link

router = Router(name="payments")


@router.message(Command("buy"))
async def cmd_buy(message: types.Message, user):
    if not user.company_id:
        await message.answer(
            "⛔ Сначала присоединитесь к компании: /create_company или /join <id>."
        )
        return

    link = await create_payment_link(
        company_id=user.company_id, plan_code="pro", months=1
    )
    await message.answer(f"Для оплаты перейдите по ссылке:\n{link}")
