import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from handlers import other, user
from config.config import load_config, Config
from utils.http_client import HttpClient


logger = logging.getLogger(__name__)

async def stop_bot():
    logger.info('Stop bot')
    await HttpClient.close_session()

async def main():
    config: Config = load_config()

    logging.basicConfig(
        level=logging.getLevelName(level=config.log.level),
        format=config.log.format
    )

    logger.info('Starting bot')
    bot = Bot(token=config.bot.token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    dp.include_router(user.router)
    dp.include_router(other.router)

    dp.shutdown.register(stop_bot)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
