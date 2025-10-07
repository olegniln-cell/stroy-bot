import enum


class UserRole(str, enum.Enum):
    manager = "manager"  # Руководитель — создаёт компанию, видит всё
    foreman = "foreman"  # Бригадир / прораб — ведёт задачи, отчёты
    worker = "worker"  # Рабочий — задачи, фото, отчёты
    client = "client"  # роль по умолчанию, минимальные права (эквивалент "guest")
    supplier = "supplier"  # Снабженец — материалы, логистика
    accountant = "accountant"  # Финансист — деньги, сметы
    admin = "admin"  # Сервисный админ


class TaskStatus(str, enum.Enum):
    todo = "todo"
    new = "new"
    in_progress = "in_progress"
    ready = "ready"


class SubscriptionStatus(str, enum.Enum):
    active = "active"
    trial = "trial"
    paused = "paused"
    canceled = "canceled"
    expired = "expired"
