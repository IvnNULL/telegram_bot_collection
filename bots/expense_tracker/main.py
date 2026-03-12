import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config.config import load_config, Config
from handlers.user import user_router
from handlers.form import form_router

logger = logging.getLogger(__name__)


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

    dp.include_router(form_router)
    dp.include_router(user_router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
