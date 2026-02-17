import aiohttp
import logging

import asyncio

logger = logging.getLogger(__name__)

async def get_gif():
    async with aiohttp.ClientSession() as session:
        async with session.get('https://yesno.wtf/api') as response:
            if response.status != 200:
                return None
            return await response.json()
