# utils/subscription_check.py
from typing import Callable, Any, Awaitable
from functools import wraps
from sqlalchemy.ext.asyncio import AsyncSession
from services.subscriptions import has_active_subscription_for_user, PermissionDenied


async def ensure_user_has_subscription(session: AsyncSession, user_id: int) -> bool:
    return await has_active_subscription_for_user(session, user_id)


def require_subscription(handler: Callable[..., Awaitable[Any]]):
    """
    Декоратор: требует активной подписки у пользователя.
    handler должен принимать (session, user_id, ...)
    """

    @wraps(handler)
    async def wrapper(*args, **kwargs):
        session: AsyncSession | None = kwargs.get("session") or (
            args[0] if args else None
        )
        user_id: int | None = kwargs.get("user_id") or (
            args[1] if len(args) > 1 else None
        )

        if session is None or user_id is None:
            raise PermissionDenied("Session or user_id not passed to decorator")

        if not await ensure_user_has_subscription(session, user_id):
            raise PermissionDenied("User has no active subscription")

        return await handler(*args, **kwargs)

    return wrapper
