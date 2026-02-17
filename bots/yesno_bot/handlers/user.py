from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command, CommandStart
from texts.texts import TEXTS
from services.services import get_gif

router = Router()


@router.message(CommandStart())
async def process_start_command(message: Message):
    await message.answer(text=TEXTS['/start'])


@router.message(Command(commands='help'))
async def process_help_command(message: Message):
    await message.answer(text=TEXTS['/help'])

@router.message(F.text)
async def process_unknown_message(message: Message):
    answer = await get_gif()
    if answer:
        await message.reply_animation(animation=answer['image'], caption=answer['answer'].capitalize())
    else:
        await message.send_copy(text=TEXTS['error'])
