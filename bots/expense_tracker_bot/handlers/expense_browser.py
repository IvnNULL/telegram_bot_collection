import logging
from contextlib import suppress
from datetime import date, datetime, timedelta

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Expense
from database.repositories import ExpenseRepository
from handlers.main_menu import send_main_menu
from keyboards.callbacks import ExpenseCallback
from keyboards.keyboards import get_browsing_kb, get_date_suggestions_kb, get_action_kb
from services.expense_service import expense_to_text, expense_dump, expenses_to_button_labels
from states.states import ExpenseEditSteps
from texts.texts import TEXTS

logger = logging.getLogger(__name__)

expense_browser_router = Router()


def prepare_edit_data(expenses: list[Expense]) -> dict:
    PAGE_SIZE = 7

    button_labels = expenses_to_button_labels(expenses)
    if not button_labels:
        return {
            'pages': [[{'text': TEXTS['edit_no_expenses'], 'index': 'pass'}]],
            'expenses_ids': [],
            'current_page': 1,
            'total_pages': 1,
        }

    pages_data = []
    for i, label in enumerate(button_labels):
        if i % PAGE_SIZE == 0:
            pages_data.append([])
        button_item = {'text': label, 'index': str(i)}
        pages_data[-1].append(button_item)

    return {
        'pages': pages_data,
        'expenses_ids': [expense.id for expense in expenses],
        'current_page': 1,
        'total_pages': len(pages_data),
    }


async def start_edit_expense(message: Message, state: FSMContext, session: AsyncSession):
    await state.set_state(ExpenseEditSteps.browsing)

    expense_repo = ExpenseRepository(session)
    latest_date = await expense_repo.get_latest_expense_date()
    if latest_date is None:
        latest_date = date.today()
    expenses = await expense_repo.get_expenses_by_date(latest_date)
    data = prepare_edit_data(expenses)

    main_message_id = await message.answer(
        text=TEXTS['edit_start'],
        reply_markup=get_browsing_kb(
            data['pages'][data['current_page'] - 1],
            data['current_page'],
            data['total_pages'],
            latest_date,
        ),
    )
    await state.update_data(main_message_id=main_message_id.message_id, date=latest_date.isoformat(), **data)


@expense_browser_router.message(StateFilter(default_state), Command(commands='edit'))
async def process_edit_command(message: Message, state: FSMContext, session: AsyncSession):
    await message.delete()
    await start_edit_expense(message, state, session)


@expense_browser_router.callback_query(StateFilter(default_state), F.data == 'expense:edit')
async def process_edit_click(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await callback.answer()
    with suppress(TelegramBadRequest):
        await callback.message.delete()
    await start_edit_expense(callback.message, state, session)


@expense_browser_router.message(StateFilter(ExpenseEditSteps), Command('cancel'))
async def process_cancel_command(message: Message, state: FSMContext):
    await message.delete()
    main_message_id = await state.get_value('main_message_id')
    try:
        await message.bot.delete_message(chat_id=message.chat.id, message_id=main_message_id)
    except TelegramBadRequest as e:
        logger.error(e)
    await state.clear()
    await send_main_menu(message)


@expense_browser_router.callback_query(StateFilter(ExpenseEditSteps), ExpenseCallback.filter(F.action == 'cancel'))
async def process_cancel_click(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await state.clear()
    await send_main_menu(callback.message)


@expense_browser_router.callback_query(StateFilter(ExpenseEditSteps), ExpenseCallback.filter(F.action == 'pass'))
async def process_pass_click(callback: CallbackQuery):
    await callback.answer()
    logger.info('PASS click')


@expense_browser_router.callback_query(
    StateFilter(ExpenseEditSteps.browsing), ExpenseCallback.filter(F.action == 'move')
)
async def process_move_click(callback: CallbackQuery, callback_data: ExpenseCallback, state: FSMContext):
    step = int(callback_data.value)
    data = await state.get_data()
    current_page = data['current_page']
    total_pages = data['total_pages']

    new_page = current_page + step
    if not 1 <= new_page <= total_pages:
        await callback.answer()
        return

    await state.update_data(current_page=new_page)
    await callback.message.edit_reply_markup(
        reply_markup=get_browsing_kb(
            data['pages'][new_page - 1],
            new_page,
            data['total_pages'],
            date.fromisoformat(data['date']),
        ),
    )


@expense_browser_router.callback_query(
    StateFilter(ExpenseEditSteps.browsing), ExpenseCallback.filter((F.action == 'change') & (F.value == 'date'))
)
async def process_change_date_click(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ExpenseEditSteps.changing_date)

    current_date_text = await state.get_value('date')
    last_date = date.fromisoformat(current_date_text) + timedelta(1)

    await callback.message.edit_text(
        text=TEXTS['change_date'],
        reply_markup=get_date_suggestions_kb(last_date=last_date),
    )


@expense_browser_router.message(StateFilter(ExpenseEditSteps.changing_date))
async def process_date_input(message: Message, state: FSMContext, session: AsyncSession):
    await message.delete()
    data = await state.get_data()
    current_date = date.fromisoformat(data['date'])
    try:
        new_date = datetime.strptime(message.text, TEXTS['DATE_FORMAT']).date()
    except ValueError:
        last_date = current_date + timedelta(1)
        return await message.bot.edit_message_text(
            text=TEXTS['change_date_incorrect'],
            chat_id=message.chat.id,
            message_id=data['main_message_id'],
            reply_markup=get_date_suggestions_kb(last_date=last_date),
        )

    if new_date != current_date:
        expense_repo = ExpenseRepository(session)
        expenses = await expense_repo.get_expenses_by_date(new_date)
        new_data = prepare_edit_data(expenses)
        await state.update_data(date=new_date.isoformat(), **new_data)
        data.update(new_data)
        current_date = new_date

    await state.set_state(ExpenseEditSteps.browsing)
    await message.bot.edit_message_text(
        text=TEXTS['edit_start'],
        chat_id=message.chat.id,
        message_id=data['main_message_id'],
        reply_markup=get_browsing_kb(
            data['pages'][data['current_page'] - 1],
            data['current_page'],
            data['total_pages'],
            current_date,
        ),
    )


@expense_browser_router.callback_query(
    StateFilter(ExpenseEditSteps.changing_date), ExpenseCallback.filter(F.action == 'select')
)
async def process_date_select(
    callback: CallbackQuery, callback_data: ExpenseCallback, state: FSMContext, session: AsyncSession
):
    new_date = datetime.strptime(callback_data.value, TEXTS['DATE_FORMAT']).date()
    current_date = date.fromisoformat(await state.get_value('date'))
    if new_date != current_date:
        expense_repo = ExpenseRepository(session)
        expenses = await expense_repo.get_expenses_by_date(new_date)
        data = prepare_edit_data(expenses)
        await state.update_data(date=new_date.isoformat(), **data)
        current_date = new_date
    else:
        data = await state.get_data()

    await state.set_state(ExpenseEditSteps.browsing)
    await callback.message.edit_text(
        text=TEXTS['edit_start'],
        reply_markup=get_browsing_kb(
            data['pages'][data['current_page'] - 1],
            data['current_page'],
            data['total_pages'],
            current_date,
        ),
    )


@expense_browser_router.callback_query(
    StateFilter(ExpenseEditSteps.browsing), ExpenseCallback.filter(F.action == 'select')
)
async def process_expense_select(
    callback: CallbackQuery, callback_data: ExpenseCallback, state: FSMContext, session: AsyncSession
):
    if callback_data.value == 'pass':
        await callback.answer()
        return

    expenses_ids = await state.get_value('expenses_ids')
    current_index = int(callback_data.value)
    expense_id = expenses_ids[current_index]
    expense_repo = ExpenseRepository(session)
    expense = await expense_repo.get_expense_by_id(expense_id)
    await state.update_data(expense=expense_dump(expense))
    await callback.message.edit_text(text=expense_to_text(expense), reply_markup=get_action_kb())


@expense_browser_router.callback_query(
    StateFilter(ExpenseEditSteps.browsing), ExpenseCallback.filter(F.action == 'return')
)
async def process_return_click(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.update_data(expense=None)
    await callback.message.edit_text(
        text=TEXTS['edit_start'],
        reply_markup=get_browsing_kb(
            data['pages'][data['current_page'] - 1],
            data['current_page'],
            data['total_pages'],
            date.fromisoformat(data['date']),
        ),
    )


@expense_browser_router.message(StateFilter(ExpenseEditSteps))
async def process_unexpected_send(message: Message):
    await message.delete()
