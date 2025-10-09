# app/handlers/start.py
import logging
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from models.user import User
from services.users import set_user_role_and_company
from utils.enums import UserRole

router = Router(name="start")
logger = logging.getLogger(__name__)

# Все роли, которые доступны в системе (для кнопок)
role_map = {
    "руководитель": UserRole.manager,
    "бригадир": UserRole.foreman,
    "рабочий": UserRole.worker,
    "клиент": UserRole.client,
    "поставщик": UserRole.supplier,
    "бухгалтер": UserRole.accountant,
}

# Рабочие роли, которые реально поддержаны сейчас
available_roles = {
    UserRole.manager,
    UserRole.foreman,
    UserRole.worker,
}


@router.message(Command("start"))
async def start_cmd(message: types.Message, user: User):
    """Хендлер на команду /start"""
    if user.company_id:
        await message.answer(
            f"Вы уже состоите в компании ID={user.company_id}.\n"
            f"Команды: /buy — оплата, /admin_company_status <id> — статус (для админов)."
        )
        return

    # Генерация кнопок из role_map
    kb = InlineKeyboardBuilder()
    for label in role_map.keys():
        kb.button(text=label.capitalize(), callback_data=f"set_role:{label}")
    kb.adjust(1)

    await message.answer(
        "👋 Добро пожаловать! Выберите вашу роль:", reply_markup=kb.as_markup()
    )


@router.callback_query(F.data.startswith("set_role:"))
async def callback_set_role(
    callback: types.CallbackQuery, session: AsyncSession, user: User
):
    """Обработка выбора роли"""

    raw_role = callback.data.split(":", 1)[1]
    role = role_map.get(raw_role)

    if not role:
        await callback.answer("Неверная роль", show_alert=True)
        return

    # Заглушка для ещё не реализованных ролей
    if role not in available_roles:
        await callback.answer("⚠️ Эта роль пока недоступна", show_alert=True)
        return

    try:
        await set_user_role_and_company(session, user.id, role)

        if role == UserRole.manager:
            txt = (
                "✅ Отлично! Теперь вы руководитель.\n"
                "Создайте вашу компанию:\n"
                "`/create_company <НазваниеКомпании>`"
            )
        else:
            txt = (
                f"✅ Отлично! Теперь вы {raw_role}.\n"
                "Чтобы присоединиться к компании, запросите ID у руководителя и используйте команду:\n"
                "`/join <ID компании>`"
            )

        await callback.message.edit_text(txt, parse_mode="Markdown")
        await callback.answer()

    except Exception:
        logger.exception("Ошибка в callback_set_role")
        await callback.answer("Произошла ошибка", show_alert=True)
