import logging

from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from keyboards.keyboards import get_main_menu_keyboard
from texts.texts import TEXTS

logger = logging.getLogger(__name__)

menu_router = Router()


async def send_main_menu(message: Message) -> None:
    await message.answer(text=TEXTS['main_menu'], reply_markup=get_main_menu_keyboard())


@menu_router.callback_query(F.data == 'main:menu')
async def process_edit_click(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass

    await send_main_menu(callback.message)
