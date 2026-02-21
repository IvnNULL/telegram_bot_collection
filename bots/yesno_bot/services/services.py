import logging
import aiofiles
from pathlib import Path
from utils.http_client import http_get

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
SAVE_DIR = BASE_DIR / 'assets'


async def save_gif(answer: str, url: str) -> None:
    folder = SAVE_DIR / answer
    folder.mkdir(parents=True, exist_ok=True)

    filename = Path(url).name
    filepath = folder / filename

    if not filepath.exists():
        data = await http_get(url)
        if data:
            async with aiofiles.open(filepath, 'wb') as f:
                await f.write(data)


async def get_answer():
    data = await http_get('https://yesno.wtf/api', as_json=True)
    logger.debug(f'API response: {data}')
    await save_gif(data['answer'], data['image'])
    return data
