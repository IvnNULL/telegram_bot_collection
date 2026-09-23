import logging
from contextlib import suppress
from datetime import date, datetime
from typing import Any

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, default_state
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from database.repositories import ExpenseRepository, PayerRepository, PlaceCategoryRepository
from keyboards.callbacks import ExpenseCallback
from keyboards.keyboards import get_add_confirmation_kb, get_suggestions_kb, get_date_suggestions_kb
from services.expense_service import expense_dict_to_text
from states.states import ExpenseAddSteps
from texts.texts import TEXTS

logger = logging.getLogger(__name__)

expense_add_router = Router()


async def update_expense_message(message: Message, state: FSMContext, suffix: str | None = None):
    data = await state.get_data()
    expense_text = expense_dict_to_text(data.get('expense_data', {}))
    if suffix:
        expense_text += f'\n\n{suffix}'
    if data.get('expense_message_id'):
        try:
            await message.bot.edit_message_text(
                text=expense_text, chat_id=message.chat.id, message_id=data['expense_message_id']
            )
        except TelegramBadRequest:
            pass
    else:
        expense_message = await message.answer(expense_text)
        await state.update_data(expense_message_id=expense_message.message_id)


async def update_step_message(
    message: Message, state: FSMContext, text: str, reply_markup: InlineKeyboardMarkup | None = None
):
    step_message_id = await state.get_value('step_message_id')
    if step_message_id:
        try:
            await message.bot.edit_message_text(
                text=text, chat_id=message.chat.id, message_id=step_message_id, reply_markup=reply_markup
            )
        except TelegramBadRequest as e:
            pass
    else:
        step_message = await message.answer(text=text, reply_markup=reply_markup)
        await state.update_data(step_message_id=step_message.message_id)


async def proceed_to_next_step(
    message: Message,
    state: FSMContext,
    expense_field: str,
    expense_value: Any,
    next_state: State,
    next_text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
):
    expense_data = await state.get_value('expense_data', {})
    expense_data.update({expense_field: expense_value})
    await state.update_data(expense_data=expense_data)

    await update_expense_message(message=message, state=state)
    await state.set_state(next_state)
    await update_step_message(message=message, state=state, text=next_text, reply_markup=reply_markup)


async def start_add_expense(message: Message, state: FSMContext):
    start_message = await message.answer(text=TEXTS['fill_start'])
    await state.update_data(start_message_id=start_message.message_id)

    await proceed_to_next_step(
        message=message,
        state=state,
        expense_field='date',
        expense_value=date.today(),
        next_state=ExpenseAddSteps.waiting_for_place,
        next_text=TEXTS['fill_place'],
    )


async def stop_add_expense(message: Message, state: FSMContext):
    data = await state.get_data()
    message_ids = [data.get('start_message_id'), data.get('expense_message_id')]
    for msg_id in message_ids:
        if msg_id:
            try:
                await message.bot.delete_message(chat_id=message.chat.id, message_id=msg_id)
            except TelegramBadRequest as e:
                logger.error(e)

    await update_step_message(
        message=message,
        state=state,
        text=f'{TEXTS["cancel_form"]}\n{TEXTS["menu_form"]}',
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text=TEXTS['main_menu:expense:add'], callback_data='expense:add'),
                    InlineKeyboardButton(text=TEXTS['main_menu:menu'], callback_data='main:menu'),
                ]
            ]
        ),
    )
    await state.clear()


@expense_add_router.message(StateFilter(default_state), Command(commands='add'))
async def process_add_command(message: Message, state: FSMContext):
    await message.delete()
    await start_add_expense(message, state)


@expense_add_router.callback_query(StateFilter(default_state), F.data == 'expense:add')
async def process_add_click(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    with suppress(TelegramBadRequest):
        await callback.message.delete()
    await start_add_expense(callback.message, state)


@expense_add_router.message(StateFilter(ExpenseAddSteps), Command(commands='cancel'))
async def process_cancel_command(message: Message, state: FSMContext):
    await message.delete()
    await stop_add_expense(message, state)


@expense_add_router.callback_query(StateFilter(ExpenseAddSteps), ExpenseCallback.filter(F.action == 'cancel'))
async def process_cancel_click(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await stop_add_expense(callback.message, state)


@expense_add_router.message(StateFilter(ExpenseAddSteps), F.text.startswith('/'))
async def process_unexpected_command(message: Message):
    await message.delete()


@expense_add_router.message(ExpenseAddSteps.waiting_for_place, F.text)
async def process_place_input(message: Message, state: FSMContext, session: AsyncSession):
    await message.delete()
    place_cat_repo = PlaceCategoryRepository(session)
    categories = await place_cat_repo.get_category_by_place(place=message.text)

    await proceed_to_next_step(
        message=message,
        state=state,
        expense_field='place',
        expense_value=message.text,
        next_state=ExpenseAddSteps.waiting_for_category,
        next_text=TEXTS['fill_category'],
        reply_markup=get_suggestions_kb('select', categories),
    )


@expense_add_router.message(ExpenseAddSteps.waiting_for_category, F.text)
async def process_category_input(message: Message, state: FSMContext):
    await message.delete()
    await proceed_to_next_step(
        message=message,
        state=state,
        expense_field='category',
        expense_value=message.text,
        next_state=ExpenseAddSteps.waiting_for_description,
        next_text=TEXTS['fill_description'],
    )


@expense_add_router.callback_query(ExpenseAddSteps.waiting_for_category, ExpenseCallback.filter(F.action == 'select'))
async def process_category_select(callback: CallbackQuery, callback_data: ExpenseCallback, state: FSMContext):
    await proceed_to_next_step(
        message=callback.message,
        state=state,
        expense_field='category',
        expense_value=callback_data.value,
        next_state=ExpenseAddSteps.waiting_for_description,
        next_text=TEXTS['fill_description'],
    )


@expense_add_router.message(ExpenseAddSteps.waiting_for_description, F.text)
async def process_description_input(message: Message, state: FSMContext):
    await message.delete()
    await proceed_to_next_step(
        message=message,
        state=state,
        expense_field='description',
        expense_value=message.text,
        next_state=ExpenseAddSteps.waiting_for_amount,
        next_text=TEXTS['fill_amount'],
    )


@expense_add_router.message(ExpenseAddSteps.waiting_for_amount, F.text)
async def process_amount_input(message: Message, state: FSMContext, session: AsyncSession):
    await message.delete()
    try:
        amount = int(float(message.text.replace(',', '.').replace(' ', '')))
    except ValueError:
        await update_step_message(message=message, state=state, text=TEXTS['fill_amount_error'])
        return

    payer_repo = PayerRepository(session)
    payers = await payer_repo.list_payers()

    await proceed_to_next_step(
        message=message,
        state=state,
        expense_field='amount',
        expense_value=amount,
        next_state=ExpenseAddSteps.waiting_for_payer,
        next_text=TEXTS['fill_payer'],
        reply_markup=get_suggestions_kb('select', payers),
    )


@expense_add_router.message(ExpenseAddSteps.waiting_for_payer, F.text)
async def process_payer_input(message: Message, state: FSMContext):
    await message.delete()
    await proceed_to_next_step(
        message=message,
        state=state,
        expense_field='payer',
        expense_value=message.text,
        next_state=ExpenseAddSteps.waiting_for_confirmation,
        next_text=TEXTS['check_form'],
        reply_markup=get_add_confirmation_kb(),
    )


@expense_add_router.callback_query(ExpenseAddSteps.waiting_for_payer, ExpenseCallback.filter(F.action == 'select'))
async def process_payer_select(callback: CallbackQuery, callback_data: ExpenseCallback, state: FSMContext):
    await proceed_to_next_step(
        message=callback.message,
        state=state,
        expense_field='payer',
        expense_value=callback_data.value,
        next_state=ExpenseAddSteps.waiting_for_confirmation,
        next_text=TEXTS['check_form'],
        reply_markup=get_add_confirmation_kb(),
    )


@expense_add_router.callback_query(
    ExpenseAddSteps.waiting_for_confirmation, ExpenseCallback.filter((F.action == 'change') & (F.value == 'date'))
)
async def process_change_date_click(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ExpenseAddSteps.waiting_for_date)
    await update_step_message(
        message=callback.message,
        state=state,
        text=TEXTS['change_date'],
        reply_markup=get_date_suggestions_kb(last_date=date.today()),
    )


@expense_add_router.message(ExpenseAddSteps.waiting_for_date, F.text)
async def process_date_input(message: Message, state: FSMContext):
    await message.delete()
    try:
        new_date = datetime.strptime(message.text, TEXTS['DATE_FORMAT']).date()
    except ValueError:
        await update_step_message(
            message=message,
            state=state,
            text=TEXTS['change_date_incorrect'],
            reply_markup=get_date_suggestions_kb(last_date=date.today()),
        )
        return

    await proceed_to_next_step(
        message=message,
        state=state,
        expense_field='date',
        expense_value=new_date,
        next_state=ExpenseAddSteps.waiting_for_confirmation,
        next_text=TEXTS['check_form'],
        reply_markup=get_add_confirmation_kb(),
    )


@expense_add_router.callback_query(ExpenseAddSteps.waiting_for_date, ExpenseCallback.filter(F.action == 'select'))
async def process_date_select(callback: CallbackQuery, callback_data: ExpenseCallback, state: FSMContext):
    new_date = datetime.strptime(callback_data.value, TEXTS['DATE_FORMAT']).date()

    await proceed_to_next_step(
        message=callback.message,
        state=state,
        expense_field='date',
        expense_value=new_date,
        next_state=ExpenseAddSteps.waiting_for_confirmation,
        next_text=TEXTS['check_form'],
        reply_markup=get_add_confirmation_kb(),
    )


@expense_add_router.callback_query(ExpenseAddSteps.waiting_for_confirmation, ExpenseCallback.filter(F.action == 'save'))
async def process_confirm_click(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    expense_repo = ExpenseRepository(session)
    payer_repo = PayerRepository(session)
    place_cat_repo = PlaceCategoryRepository(session)

    expense_data = data['expense_data']
    await expense_repo.add_expense(user_id=callback.from_user.id, **expense_data)
    await payer_repo.add_payer(payer=expense_data['payer'])
    await place_cat_repo.add_place_category(place=expense_data['place'], category=expense_data['category'])

    await update_expense_message(message=callback.message, state=state, suffix=TEXTS['save_form'])
    await update_step_message(
        message=callback.message,
        state=state,
        text=TEXTS['menu_form'],
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text=TEXTS['main_menu:expense:add'], callback_data='expense:add'),
                    InlineKeyboardButton(text=TEXTS['main_menu:menu'], callback_data='main:menu'),
                ]
            ]
        ),
    )

    with suppress(TelegramBadRequest):
        await callback.message.bot.delete_message(chat_id=callback.message.chat.id, message_id=data['start_message_id'])
    await state.clear()


@expense_add_router.message(StateFilter(ExpenseAddSteps))
async def process_unexpected_send(message: Message):
    # await message.answer(text=TEXTS['fill_wrong'])
    await message.delete()
