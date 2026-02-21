from aiogram import Router
from aiogram.types import Message
from texts.texts import TEXTS

router = Router()


@router.message()
async def process_unknown_message(message: Message):
    await message.answer(text=TEXTS['no_text'])
