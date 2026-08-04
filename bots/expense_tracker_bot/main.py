import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommandScopeDefault
from config.config import Config, load_config
from database.connection import create_session_maker
from handlers.form import form_router
from handlers.place_categories import pc_router
from handlers.user import user_router
from keyboards.menu_button import DEFAULT_COMMANDS
from middlewares.access import AccessMiddleware
from middlewares.database import DatabaseMiddleware

logger = logging.getLogger(__name__)


async def on_startup(bot: Bot):
    logging.info('Setting up default commands.')
    await bot.set_my_commands(commands=DEFAULT_COMMANDS, scope=BotCommandScopeDefault())


async def main():
    config: Config = load_config()

    logging.basicConfig(
        level=logging.getLevelName(level=config.log.level),
        format=config.log.format,
    )

    storage = MemoryStorage()

    logger.info('Starting bot...')
    bot = Bot(token=config.bot.token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=storage)

    allow_ids = config.bot.allow_ids
    session_factory = create_session_maker(config.db.url)

    logger.info('Including middlewares...')
    dp.update.middleware(AccessMiddleware(allow_ids))
    dp.update.middleware(DatabaseMiddleware(session_factory))

    logger.info('Including routers...')
    dp.include_router(form_router)
    dp.include_router(pc_router)
    dp.include_router(user_router)

    dp.startup.register(on_startup)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
