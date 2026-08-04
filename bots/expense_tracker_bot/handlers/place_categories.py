import csv
import io
import logging

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, BufferedInputFile
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from database.models import PlaceCategory
from database.repositories import PlaceCategoryRepository

logger = logging.getLogger(__name__)

pc_router = Router()


@pc_router.message(Command(commands='get_pc'))
async def process_get_pc_command(message: Message, session: AsyncSession):
    pc_repo = PlaceCategoryRepository(session)
    all_data = await pc_repo.get_all_data()

    csv_text = 'place;category;counter\n'
    if all_data:
        csv_text += '\n'.join(f'{row.place};{row.category};{row.counter}' for row in all_data)

    file_bytes = csv_text.encode('utf-8-sig')
    csv_file = BufferedInputFile(file_bytes, filename='place_categories.csv')
    await message.answer_document(document=csv_file)


@pc_router.message(F.document, Command(commands='update_pc'))
async def process_update_pc_command(message: Message, bot: Bot, session: AsyncSession):
    try:
        file_in_memory = io.BytesIO()
        await bot.download(file=message.document.file_id, destination=file_in_memory)
        file_in_memory.seek(0)

        csv_stream = io.TextIOWrapper(file_in_memory, encoding='utf-8-sig')
        csv_reader = csv.DictReader(csv_stream, delimiter=';')

        pc_list: list[PlaceCategory] = []
        for row in csv_reader:
            pc_list.append(
                PlaceCategory(
                    place=row['place'],
                    category=row['category'],
                    counter=int(row['counter']),
                )
            )

        pc_repo = PlaceCategoryRepository(session)
        await pc_repo.update(pc_list)

        await message.answer(text='Ok')
    except Exception as e:
        logger.error(e)
        await message.answer(text='error')
