import logging
from datetime import date, datetime, timedelta

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import CallbackQuery, Message
from database.repositories import ExpenseRepository
from keyboards.keyboards import get_date_keyboard, get_expenses_keyboard
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

    main_message_id = await message.answer(
        text=TEXTS['edit_start'],
        reply_markup=get_expenses_keyboard(
            data['expenses_buttons'][data['current_page'] - 1],
            data['current_page'],
            data['total_pages'],
            latest_date,
        ),
    )
    await state.update_data(main_message_id=main_message_id.message_id, date=latest_date.isoformat(), **data)


@edit_router.message(StateFilter(FSMEditExpense), Command('cancel'))
async def process_cancel_command(message: Message, state: FSMContext):
    await message.delete()
    main_message_id = await state.get_value('main_message_id')
    try:
        await message.bot.delete_message(chat_id=message.chat.id, message_id=main_message_id)
    except TelegramBadRequest as e:
        logger.error(e)
    await state.clear()


@edit_router.callback_query(StateFilter(FSMEditExpense), F.data == 'cancel')
async def process_cancel_click(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await state.clear()


@edit_router.callback_query(StateFilter(FSMEditExpense), F.data == 'pass')
async def process_pass_click(callback: CallbackQuery):
    await callback.answer()


@edit_router.callback_query(StateFilter(FSMEditExpense.browsing), F.data.startswith('move:'))
async def process_move_click(callback: CallbackQuery, state: FSMContext):
    step = int(callback.data.split(':')[-1])
    data = await state.get_data()
    current_page = data['current_page']
    total_pages = data['total_pages']

    new_page = current_page + step
    if not 1 <= new_page <= total_pages:
        return callback.answer()

    await state.update_data(current_page=new_page)
    await callback.message.edit_reply_markup(
        reply_markup=get_expenses_keyboard(
            data['expenses_buttons'][new_page - 1],
            new_page,
            data['total_pages'],
            date.fromisoformat(data['date']),
        ),
    )


@edit_router.callback_query(StateFilter(FSMEditExpense.browsing), F.data == 'change_date')
async def process_change_date_click(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FSMEditExpense.changing_date)

    current_date_text = await state.get_value('date')
    start_date = date.fromisoformat(current_date_text) - timedelta(1)

    await callback.message.edit_text(
        text=TEXTS['change_date'],
        reply_markup=get_date_keyboard(start_date=start_date, prefix='select_date:'),
    )


@edit_router.callback_query(StateFilter(FSMEditExpense.changing_date), F.data.startswith('select_date'))
async def process_date_click(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    new_date = datetime.strptime(callback.data.split(':')[-1], TEXTS['DATE_FORMAT']).date()
    current_date = date.fromisoformat(await state.get_value('date'))
    if new_date != current_date:
        expense_repo = ExpenseRepository(session)
        expenses = await expense_repo.get_expenses_by_date(new_date)
        data = prepare_edit_data(expenses)
        await state.update_data(date=new_date.isoformat(), **data)
        current_date = new_date
    else:
        data = await state.get_data()

    await state.set_state(FSMEditExpense.browsing)
    await callback.message.edit_text(
        text=TEXTS['edit_start'],
        reply_markup=get_expenses_keyboard(
            data['expenses_buttons'][data['current_page'] - 1],
            data['current_page'],
            data['total_pages'],
            current_date,
        ),
    )


@edit_router.message(StateFilter(FSMEditExpense.changing_date))
async def process_date_send(message: Message, state: FSMContext, session: AsyncSession):
    await message.delete()
    data = await state.get_data()
    current_date = date.fromisoformat(data['date'])
    try:
        new_date = datetime.strptime(message.text, TEXTS['DATE_FORMAT']).date()
    except ValueError:
        start_date = current_date - timedelta(1)
        return await message.bot.edit_message_text(
            text=TEXTS['change_date_incorrect'],
            chat_id=message.chat.id,
            message_id=data['main_message_id'],
            reply_markup=get_date_keyboard(start_date=start_date, prefix='select_date:'),
        )

    if new_date != current_date:
        expense_repo = ExpenseRepository(session)
        expenses = await expense_repo.get_expenses_by_date(new_date)
        new_data = prepare_edit_data(expenses)
        await state.update_data(**new_data)
        data.update(new_data)
        current_date = new_date

    await state.set_state(FSMEditExpense.browsing)
    await message.bot.edit_message_text(
        text=TEXTS['edit_start'],
        chat_id=message.chat.id,
        message_id=data['main_message_id'],
        reply_markup=get_expenses_keyboard(
            data['expenses_buttons'][data['current_page'] - 1],
            data['current_page'],
            data['total_pages'],
            current_date,
        ),
    )


@edit_router.callback_query(StateFilter(FSMEditExpense))
async def process_click(callback: CallbackQuery):
    await callback.answer()


@edit_router.message(StateFilter(FSMEditExpense))
async def process_wrong_send(message: Message):
    await message.delete()
