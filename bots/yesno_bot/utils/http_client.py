import aiohttp
import logging

logger = logging.getLogger(__name__)

class HttpClient:
    _session = None

    @classmethod
    async def get_session(cls):
        if cls._session is None or cls._session.closed:
            logger.info('New session')
            cls._session = aiohttp.ClientSession()
        return cls._session

    @classmethod
    async def close_session(cls):
        if cls._session and not cls._session.closed:
            logger.info("Closing session")
            await cls._session.close()
