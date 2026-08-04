import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User

logger = logging.getLogger(__name__)


class AccessMiddleware(BaseMiddleware):
    def __init__(self, allow_ids: list[int]):
        self._allow_ids = allow_ids

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user: User = data.get('event_from_user')
        if not user or user.id not in self._allow_ids:
            logger.info(f'Unidentified user with ID {user.id}')
            return None

        return await handler(event, data)
