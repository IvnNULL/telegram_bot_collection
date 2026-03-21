import logging
from typing import Awaitable, Any, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User

logger = logging.getLogger(__name__)


class AccessMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: dict[str, Any]
    ) -> Any:
        user: User = data.get('event_from_user')
        if user.id not in data['allow_id']:
            logger.info(f'Unidentified user with ID {user.id}')
            return None

        return await handler(event, data)
