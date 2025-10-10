# saas_bot/core/context.py
import contextvars

# Уникальный ID запроса (генерируется для каждого апдейта)
request_id = contextvars.ContextVar("request_id", default=None)

# ID пользователя Telegram (если есть)
user_id = contextvars.ContextVar("user_id", default=None)

# ID компании (если известно в бизнес-логике)
company_id = contextvars.ContextVar("company_id", default=None)
