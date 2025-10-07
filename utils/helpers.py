# utils/helpers.py
from datetime import datetime
from models.project import Project
from models.task import Task


def format_project_list(projects: list[Project]) -> str:
    """
    Форматирует список проектов в читаемый текст.
    """
    if not projects:
        return "Проекты не найдены."

    formatted_list = [f"{p.id}. {p.name}" for p in projects]
    return "Список проектов:\n" + "\n".join(formatted_list)


def format_tasks_list(tasks: list[Task]) -> str:
    """
    Форматирует список задач в читаемый текст.
    """
    if not tasks:
        return "Задачи не найдены."

    text = "Список задач:\n"
    for task in tasks:
        # Проверяем, что объект project существует, чтобы избежать ошибок
        project_name = task.project.name if task.project else "Неизвестный проект"
        text += f"\nЗадача ID: {task.id}\n"
        text += f"  - Название: {task.title}\n"
        text += f"  - Проект: {project_name}\n"
        text += f"  - Статус: {task.status}\n"

    return text


def get_current_time_str() -> str:
    """
    Возвращает текущее время в строковом формате.
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
