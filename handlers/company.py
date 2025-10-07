import logging
from aiogram import Router, types, F
from sqlalchemy.ext.asyncio import AsyncSession
from services.companies import create_company as svc_create_company
from models import Company
from utils.enums import UserRole
from services.audit import log_action

router = Router(name="company")
logger = logging.getLogger(__name__)


@router.message(F.text.regexp(r"^/create_company\s+.+"))
async def create_company_cmd(message: types.Message, session: AsyncSession, user):
    if user.company_id:
        await message.answer("⛔ Вы уже состоите в компании.")
        return

    company_name = message.text.split(maxsplit=1)[1].strip()
    try:
        company = await svc_create_company(session, company_name, user.id)
        user.company_id = company.id
        user.role = UserRole.manager  # создатель компании = руководитель
        session.add(user)
        await session.commit()

        # Добавляем логирование
        await log_action(
            session,
            actor_user_id=user.id,
            actor_tg_id=user.tg_id,
            action="create_company",
            entity_type="Company",
            entity_id=company.id,
            payload={"name": company.name},
        )

        logger.info(
            "Компания %s (%s) создана пользователем %s",
            company.id,
            company.name,
            user.tg_id,
        )

        await message.answer(
            f"Компания '{company.name}' успешно создана!\n"
            f"Ваш ID компании: {company.id}."
        )
    except Exception as e:
        await session.rollback()
        logger.exception("Ошибка при создании компании: %s", e)
        await message.answer("⚠️ Ошибка при создании компании. Попробуйте ещё раз.")


@router.message(F.text.regexp(r"^/join\s+\d+(\s+(рабочий|бригадир))?$"))
async def join_company_cmd(message: types.Message, session: AsyncSession, user):
    if user.company_id:
        await message.answer("Вы уже состоите в компании.")
        return

    parts = message.text.split()
    company_id = int(parts[1])
    role_str = parts[2] if len(parts) > 2 else "рабочий"

    company = await session.get(Company, company_id)
    if not company:
        await message.answer("Компания не найдена.")
        return

    try:
        role_map = {
            "рабочий": UserRole.worker,
            "бригадир": UserRole.foreman,
        }

        role_enum = role_map.get(role_str.lower())
        if not role_enum:
            await message.answer("⚠️ Неверная роль. Доступные роли: рабочий, бригадир.")
            return

        user.company_id = company.id
        user.role = role_enum
        session.add(user)
        await session.commit()

        # Добавляем логирование
        await log_action(
            session,
            actor_user_id=user.id,
            actor_tg_id=user.tg_id,
            action="join_company",
            entity_type="Company",
            entity_id=company.id,
            payload={"role": role_enum.name, "user_tg_id": user.tg_id},
        )

        logger.info(
            "Пользователь %s присоединился к компании %s как %s",
            user.tg_id,
            company.id,
            role_enum.name,
        )

        if len(parts) > 2:
            await message.answer(
                f"✅ Вы присоединились к компании '{company.name}' (ID={company.id}) как {role_enum.name.capitalize()}."
            )
        else:
            await message.answer(
                f"✅ Вы присоединились к компании '{company.name}' (ID={company.id}) как рабочий.\n\n"
                f"Если вы должны быть бригадиром — используйте команду:\n"
                f"`/join {company.id} бригадир`",
                parse_mode="Markdown",
            )
    except Exception as e:
        await session.rollback()
        logger.exception("Ошибка при присоединении: %s", e)
        await message.answer("⚠️ Ошибка при присоединении. Попробуйте ещё раз.")
