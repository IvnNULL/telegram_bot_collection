import logging
from datetime import date

from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import Message, CallbackQuery
from database.repositories import ExpenseRepository
from keyboards.keyboards import get_expenses_keyboard
from services.expense_service import prepare_edit_data
from sqlalchemy.ext.asyncio import AsyncSession
from states.states import FSMEditExpense
from texts.texts import TEXTS

logger = logging.getLogger(__name__)

edit_router = Router()


@edit_router.message(StateFilter(default_state), Command(commands='edit'))
async def process_edit_command(message: Message, state: FSMContext, session: AsyncSession):
    await message.delete()
    await state.set_state(FSMEditExpense.browsing)

    expense_repo = ExpenseRepository(session)
    latest_date = await expense_repo.get_latest_expense_date()
    if latest_date is None:
        latest_date = date.today()
    expenses = await expense_repo.get_expenses_by_date(latest_date)
    data = prepare_edit_data(expenses)

    edit_message = await message.answer(
        text=TEXTS['edit_start'],
        reply_markup=get_expenses_keyboard(
            data['expenses_buttons'][data['current_page'] - 1],
            data['current_page'],
            data['total_pages'],
            latest_date,
        ),
    )
    await state.update_data(edit_message_id=edit_message.message_id, date=latest_date.isoformat(), **data)


@edit_router.message(StateFilter(FSMEditExpense), Command('cancel'))
async def process_cancel_command(message: Message, state: FSMContext):
    await message.delete()
    edit_message_id = await state.get_value('edit_message_id')
    try:
        await message.bot.delete_message(chat_id=message.chat.id, message_id=edit_message_id)
    except TelegramBadRequest as e:
        logger.error(e)
    await state.clear()


@edit_router.callback_query(StateFilter(FSMEditExpense), F.data == 'cancel')
async def process_cancel_click(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await state.clear()


@edit_router.callback_query(StateFilter(FSMEditExpense))
async def process_click(callback: CallbackQuery):
    await callback.answer()


@edit_router.message(StateFilter(FSMEditExpense))
async def process_wrong_send(message: Message):
    await message.delete()
