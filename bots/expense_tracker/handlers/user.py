import logging

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from texts.texts import TEXTS

logger = logging.getLogger(__name__)

router = Router()


@router.message(CommandStart())
async def process_start_command(message: Message):
    await message.answer(text=TEXTS['/start'])


@router.message(Command(commands='help'))
async def process_start_command(message: Message):
    await message.answer(text=TEXTS['/help'])
