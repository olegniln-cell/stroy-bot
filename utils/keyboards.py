from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)


def get_role_selection_keyboard():
    buttons = [
        [
            InlineKeyboardButton(
                text="Руководитель", callback_data="set_role:руководитель"
            ),
            InlineKeyboardButton(text="Бригадир", callback_data="set_role:бригадир"),
        ],
        [InlineKeyboardButton(text="Рабочий", callback_data="set_role:рабочий")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """
    Создает основное меню.
    """
    buttons = [
        [KeyboardButton(text="/projects"), KeyboardButton(text="/tasks")],
        [KeyboardButton(text="/reports")],
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def get_task_status_keyboard():
    buttons = [
        [InlineKeyboardButton(text="Назначено", callback_data="status_assigned")],
        [InlineKeyboardButton(text="В работе", callback_data="status_in_progress")],
        [InlineKeyboardButton(text="Завершено", callback_data="status_done")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_tasks_keyboard(tasks):
    buttons = [
        [
            InlineKeyboardButton(
                text=f"Задача: {task.title}", callback_data=f"show_task:{task.id}"
            )
        ]
        for task in tasks
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_task_options_keyboard(task_id):
    buttons = [
        [
            InlineKeyboardButton(
                text="Взять в работу", callback_data=f"take_task:{task_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="Завершить", callback_data=f"complete_task:{task_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="Отказаться", callback_data=f"decline_task:{task_id}"
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_company_management_keyboard():
    buttons = [
        [InlineKeyboardButton(text="Добавить пользователя", callback_data="add_user")],
        [InlineKeyboardButton(text="Изменить роль", callback_data="change_role")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_confirm_keyboard():
    buttons = [
        [
            InlineKeyboardButton(text="Да", callback_data="confirm"),
            InlineKeyboardButton(text="Нет", callback_data="cancel"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_project_creation_keyboard():
    buttons = [
        [
            InlineKeyboardButton(
                text="Создать проект", callback_data="create_project_start"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
