import logging

from aiogram import Router, Bot
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from services.expense_service import get_expenses_text, get_expenses_csv_text
from texts.texts import TEXTS

logger = logging.getLogger(__name__)

user_router = Router()


@user_router.message(CommandStart())
async def process_start_command(message: Message, bot: Bot):
    await message.answer(text=TEXTS['/start'])


@user_router.message(Command(commands='help'))
async def process_start_command(message: Message):
    await message.answer(text=TEXTS['/help'])


@user_router.message(Command(commands='show'))
async def process_show_command(message: Message, session_factory: async_sessionmaker[AsyncSession]):
    async with session_factory() as session:
        text = await get_expenses_text(session)
    await message.answer(text=text)


@user_router.message(Command(commands='show_csv'))
async def process_show_command(message: Message, session_factory: async_sessionmaker[AsyncSession]):
    async with session_factory() as session:
        text = await get_expenses_csv_text(session)
    await message.answer(text=text)


@user_router.message()
async def process_other_message(message: Message):
    await message.answer(text=TEXTS['other'])
