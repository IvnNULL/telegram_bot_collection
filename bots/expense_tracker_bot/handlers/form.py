import logging
from datetime import date, datetime
from typing import Any

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, default_state
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from database.repositories import ExpenseRepository, PayerRepository, PlaceCategoryRepository
from handlers.main_menu import send_main_menu
from keyboards.keyboards import create_inline_keyboard, get_date_inline_keyboard, get_save_form_keyboard
from sqlalchemy.ext.asyncio import AsyncSession
from states.states import FSMFillForm
from texts.texts import TEXTS

logger = logging.getLogger(__name__)

form_router = Router()


def get_expense_text(expense_dict: dict) -> str:
    return (
        f'Дата: {expense_dict["exp_date"].strftime("%d.%m.%Y")}\n'
        f'Место: {expense_dict.get("place", "")}\n'
        f'Категория: {expense_dict.get("category", "")}\n'
        f'Описание: {expense_dict.get("description", "")}\n'
        f'Сумма: {expense_dict.get("amount", "")}\n'
        f'Плательщик: {expense_dict.get("payer", "")}'
    )


async def start_add_expense(message: Message, state: FSMContext):
    start_message = await message.answer(text=TEXTS['fill_start'])
    await state.update_data(start_message_id=start_message.message_id)

    await proceed_to_next_step(
        event=message,
        state=state,
        expense_field='exp_date',
        expense_value=date.today(),
        next_state=FSMFillForm.fill_place,
        next_text=TEXTS['fill_place'],
    )


async def update_expense_message(message: Message, state: FSMContext):
    data = await state.get_data()
    expense_text = get_expense_text(data.get('expense_data', {}))
    if data.get('expense_message_id'):
        await message.bot.edit_message_text(
            text=expense_text, chat_id=message.chat.id, message_id=data['expense_message_id']
        )
    else:
        expense_message = await message.answer(expense_text)
        await state.update_data(expense_message_id=expense_message.message_id)


async def update_state_message(
    message: Message, state: FSMContext, *, text: str, reply_markup: InlineKeyboardMarkup | None = None
):
    state_message_id = await state.get_value('state_message_id')
    if state_message_id:
        try:
            await message.bot.edit_message_text(
                text=text, chat_id=message.chat.id, message_id=state_message_id, reply_markup=reply_markup
            )
        except TelegramBadRequest as e:
            logger.error(e)
    else:
        state_message = await message.answer(text=text, reply_markup=reply_markup)
        await state.update_data(state_message_id=state_message.message_id)


async def proceed_to_next_step(
    event: Message | CallbackQuery,
    state: FSMContext,
    expense_field: str,
    expense_value: Any,
    next_state: State,
    next_text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
):
    if isinstance(event, Message):
        await event.delete()
        message = event
    else:
        message = event.message

    expense_data = await state.get_value('expense_data', {})
    expense_data.update({expense_field: expense_value})
    await state.update_data(expense_data=expense_data)

    await update_expense_message(message, state)
    await state.set_state(next_state)
    await update_state_message(message, state, text=next_text, reply_markup=reply_markup)


@form_router.message(StateFilter(FSMFillForm), Command(commands='cancel'))
@form_router.callback_query(StateFilter(FSMFillForm.save_form), F.data == 'cancel_form')
async def process_cancel_command(event: Message | CallbackQuery, state: FSMContext):
    if isinstance(event, Message):
        await event.delete()
        message = event
    else:
        message = event.message

    data = await state.get_data()
    message_ids = [data.get('start_message_id'), data.get('expense_message_id')]
    for msg_id in message_ids:
        if msg_id:
            try:
                await message.bot.delete_message(chat_id=message.chat.id, message_id=msg_id)
            except TelegramBadRequest as e:
                logger.error(e)

    await update_state_message(message, state, text=TEXTS['cancel_form'])
    await state.clear()
    await send_main_menu(message)


@form_router.message(StateFilter(default_state), Command(commands='add'))
async def process_add_command(message: Message, state: FSMContext):
    await start_add_expense(message, state)


@form_router.callback_query(StateFilter(default_state), F.data == 'expense:add')
async def process_add_click(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await start_add_expense(callback.message, state)


@form_router.message(StateFilter(FSMFillForm), F.text.startswith('/'))
async def process_other_command(message: Message):
    await message.delete()


@form_router.message(StateFilter(FSMFillForm.fill_place), F.text)
async def process_place_send(message: Message, state: FSMContext, session: AsyncSession):
    place_cat_repo = PlaceCategoryRepository(session)
    categories = await place_cat_repo.get_category_by_place(place=message.text)

    await proceed_to_next_step(
        event=message,
        state=state,
        expense_field='place',
        expense_value=message.text,
        next_state=FSMFillForm.fill_category,
        next_text=TEXTS['fill_category'],
        reply_markup=create_inline_keyboard(categories, 'category_'),
    )


@form_router.message(StateFilter(FSMFillForm.fill_category), F.text)
async def process_category_send(message: Message, state: FSMContext):
    await proceed_to_next_step(
        event=message,
        state=state,
        expense_field='category',
        expense_value=message.text,
        next_state=FSMFillForm.fill_description,
        next_text=TEXTS['fill_description'],
    )


@form_router.callback_query(StateFilter(FSMFillForm.fill_category), F.data.startswith('category_'))
async def process_category_click(callback: CallbackQuery, state: FSMContext):
    data = callback.data.removeprefix('category_')

    await proceed_to_next_step(
        event=callback,
        state=state,
        expense_field='category',
        expense_value=data,
        next_state=FSMFillForm.fill_description,
        next_text=TEXTS['fill_description'],
    )


@form_router.message(StateFilter(FSMFillForm.fill_description), F.text)
async def process_description_send(message: Message, state: FSMContext):
    await proceed_to_next_step(
        event=message,
        state=state,
        expense_field='description',
        expense_value=message.text,
        next_state=FSMFillForm.fill_amount,
        next_text=TEXTS['fill_amount'],
    )


@form_router.message(StateFilter(FSMFillForm.fill_amount), F.text)
async def process_amount_send(message: Message, state: FSMContext, session: AsyncSession):
    try:
        amount = int(float(message.text.replace(',', '.').replace(' ', '')))
    except ValueError:
        await message.delete()
        await update_state_message(message, state, text=TEXTS['fill_amount_error'])
        return

    payer_repo = PayerRepository(session)
    payers = await payer_repo.list_payers()

    await proceed_to_next_step(
        event=message,
        state=state,
        expense_field='amount',
        expense_value=amount,
        next_state=FSMFillForm.fill_payer,
        next_text=TEXTS['fill_payer'],
        reply_markup=create_inline_keyboard(payers, 'payers_'),
    )


@form_router.message(StateFilter(FSMFillForm.fill_payer), F.text)
async def process_payer_send(message: Message, state: FSMContext):
    await proceed_to_next_step(
        event=message,
        state=state,
        expense_field='payer',
        expense_value=message.text,
        next_state=FSMFillForm.save_form,
        next_text=TEXTS['check_form'],
        reply_markup=get_save_form_keyboard(),
    )


@form_router.callback_query(StateFilter(FSMFillForm.fill_payer), F.data.startswith('payers_'))
async def process_payer_click(callback: CallbackQuery, state: FSMContext):
    data = callback.data.removeprefix('payers_')

    await proceed_to_next_step(
        event=callback,
        state=state,
        expense_field='payer',
        expense_value=data,
        next_state=FSMFillForm.save_form,
        next_text=TEXTS['check_form'],
        reply_markup=get_save_form_keyboard(),
    )


@form_router.callback_query(StateFilter(FSMFillForm.save_form), F.data == 'change_date_form')
async def process_change_date_click(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FSMFillForm.change_date)
    await update_state_message(
        callback.message,
        state,
        text=TEXTS['change_date'],
        reply_markup=get_date_inline_keyboard(
            '%d.%m.%Y',
            'date_',
        ),
    )


@form_router.message(StateFilter(FSMFillForm.change_date), F.text)
async def process_date_send(message: Message, state: FSMContext):
    try:
        new_date = datetime.strptime(message.text, '%d.%m.%Y')
    except ValueError:
        await message.delete()
        await update_state_message(
            message,
            state,
            text=TEXTS['change_date_incorrect'],
            reply_markup=get_date_inline_keyboard('%d.%m.%Y', 'date_'),
        )
        logger.error('Incorrect date')
        return

    await proceed_to_next_step(
        event=message,
        state=state,
        expense_field='exp_date',
        expense_value=new_date,
        next_state=FSMFillForm.save_form,
        next_text=TEXTS['check_form'],
        reply_markup=get_save_form_keyboard(),
    )


@form_router.callback_query(StateFilter(FSMFillForm.change_date), F.data.startswith('date_'))
async def process_date_click(callback: CallbackQuery, state: FSMContext):
    data = callback.data.removeprefix('date_')
    new_date = datetime.strptime(data, '%d.%m.%Y')

    await proceed_to_next_step(
        event=callback,
        state=state,
        expense_field='exp_date',
        expense_value=new_date,
        next_state=FSMFillForm.save_form,
        next_text=TEXTS['check_form'],
        reply_markup=get_save_form_keyboard(),
    )


@form_router.callback_query(StateFilter(FSMFillForm.save_form), F.data == 'save_form')
async def process_save_form_click(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    expense_repo = ExpenseRepository(session)
    payer_repo = PayerRepository(session)
    place_cat_repo = PlaceCategoryRepository(session)

    expense_data = data['expense_data']
    await expense_repo.add_expense(user_id=callback.from_user.id, **expense_data)
    await payer_repo.add_payer(payer=expense_data['payer'])
    await place_cat_repo.add_place_category(place=expense_data['place'], category=expense_data['category'])

    await callback.message.edit_text(text=TEXTS['save_form'])

    if data['start_message_id']:
        try:
            await callback.message.bot.delete_message(
                chat_id=callback.message.chat.id, message_id=data['start_message_id']
            )
        except TelegramBadRequest as e:
            logger.error(e)

    await state.clear()
    await send_main_menu(callback.message)


@form_router.message(StateFilter(FSMFillForm))
async def process_wrong_send(message: Message):
    # await message.answer(text=TEXTS['fill_wrong'])
    await message.delete()
