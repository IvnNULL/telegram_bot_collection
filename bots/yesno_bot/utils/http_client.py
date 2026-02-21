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
            logger.info('Closing session')
            await cls._session.close()


async def http_get(url, as_json=False, timeout=10):
    session = await HttpClient.get_session()
    try:
        async with session.get(url, timeout=timeout) as response:
            response.raise_for_status()
            if as_json:
                return await response.json()
            return await response.read()
    except TimeoutError:
        logger.error(f'Timeout error - {timeout}s: {url}')
    except aiohttp.ClientError as e:
        logger.error(f'HTTP error: {e}')
