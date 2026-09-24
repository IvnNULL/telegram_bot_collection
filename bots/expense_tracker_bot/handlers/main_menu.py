import logging
from contextlib import suppress

from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from database.repositories import ExpenseRepository
from keyboards.callbacks import MenuCallback
from keyboards.keyboards import get_main_menu_keyboard, get_show_menu_kb
from services.expense_service import expenses_to_csv_text, text_to_csv_file
from texts.texts import TEXTS

logger = logging.getLogger(__name__)

menu_router = Router()


async def send_main_menu(message: Message) -> None:
    await message.answer(text=TEXTS['main_menu'], reply_markup=get_main_menu_keyboard())


@menu_router.callback_query(MenuCallback.filter(F.target == 'main'))
async def process_main_click(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    with suppress(TelegramBadRequest):
        await callback.message.delete()

    await send_main_menu(callback.message)


@menu_router.callback_query(MenuCallback.filter(F.target == 'show_menu'))
async def process_show_menu_click(callback: CallbackQuery):
    await callback.answer()
    with suppress(TelegramBadRequest):
        await callback.message.delete_reply_markup()

    await send_main_menu(callback.message)


@menu_router.callback_query(MenuCallback.filter(F.target == 'export'))
async def process_export_click(callback: CallbackQuery, session: AsyncSession):
    await callback.answer()
    with suppress(TelegramBadRequest):
        await callback.message.delete()

    expense_repo = ExpenseRepository(session)
    expenses = await expense_repo.list_expenses()

    text = expenses_to_csv_text(expenses)
    csv_file = text_to_csv_file(text)
    await callback.message.answer_document(document=csv_file, reply_markup=get_show_menu_kb())

