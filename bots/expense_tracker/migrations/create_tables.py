import asyncio
import logging
from database.connection import create_db
from database.models import Base
from config.config import Config, load_config

config: Config = load_config()

logging.basicConfig(
    level=logging.getLevelName(level=config.log.level),
    format=config.log.format,
)

logger = logging.getLogger(__name__)


async def main():
   async_engine, _ = create_db(config.db.url)

   async with async_engine.connect() as conn:
       await conn.run_sync(Base.metadata.create_all)

if __name__ == '__main__':
    asyncio.run(main())