import logging
from utils.http_client import HttpClient

logger = logging.getLogger(__name__)


async def get_gif():
    session = await HttpClient.get_session()
    async with session.get('https://yesno.wtf/api') as response:
        if response.status != 200:
            return None
        return await response.json()
