import logging
from contextlib import suppress
from datetime import timedelta, datetime
from typing import Any

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from database.repositories import ExpenseRepository, PlaceCategoryRepository
from handlers.main_menu import send_main_menu
from keyboards.callbacks import ExpenseCallback
from keyboards.keyboards import get_edit_fields_kb, get_date_suggestions_kb, get_suggestions_kb
from services.expense_service import expense_dict_to_text
from states.states import ExpenseEditSteps
from texts.texts import TEXTS

logger = logging.getLogger(__name__)

expense_edit_router = Router()


async def update_expense_data(expense_field: str, expense_value: Any, state: FSMContext) -> None:
    expense_data = await state.get_value('expense', {})
    expense_data.update({expense_field: expense_value})
    await state.update_data(expense=expense_data)


async def update_expense_message(message: Message, state: FSMContext, prefix: str | None = None) -> None:
    data = await state.get_data()
    expense_text = expense_dict_to_text(data['expense'])
    if prefix:
        expense_text = f'{prefix}\n\n{expense_text}'
    with suppress(TelegramBadRequest):
        await message.bot.edit_message_text(
            text=expense_text, chat_id=message.chat.id, message_id=data['main_message_id']
        )


async def update_step_message(
    message: Message, state: FSMContext, text: str, reply_markup: InlineKeyboardMarkup | None = None
) -> None:
    step_message_id = await state.get_value('step_message_id')
    with suppress(TelegramBadRequest):
        await message.bot.edit_message_text(
            text=text, chat_id=message.chat.id, message_id=step_message_id, reply_markup=reply_markup
        )


@expense_edit_router.callback_query(ExpenseEditSteps.browsing, ExpenseCallback.filter(F.action == 'edit'))
async def process_edit_click(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete_reply_markup()

    data = await state.get_data()
    data.pop('pages')
    step_message = await callback.message.answer(text=TEXTS['edit_text'], reply_markup=get_edit_fields_kb())
    data['step_message_id'] = step_message.message_id

    await state.set_data(data)
    await state.set_state(ExpenseEditSteps.editing)


@expense_edit_router.callback_query(ExpenseEditSteps.editing, ExpenseCallback.filter(F.action == 'cancel'))
async def process_cancel_click(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()

    main_message_id = await state.get_value('main_message_id')
    with suppress(TelegramBadRequest):
        await callback.message.bot.delete_message(chat_id=callback.message.chat.id, message_id=main_message_id)

    await state.clear()
    await send_main_menu(callback.message)


@expense_edit_router.callback_query(ExpenseEditSteps.editing, ExpenseCallback.filter(F.action == 'save'))
async def process_save_click(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await callback.answer()

    expense_data = await state.get_value('expense')
    expense_repo = ExpenseRepository(session)
    await expense_repo.update_expense(expense_data)
    await session.commit()

    await update_expense_message(callback.message, state, prefix=TEXTS['success_edit'])
    await callback.message.delete()
    await state.clear()
    await send_main_menu(callback.message)


@expense_edit_router.callback_query(ExpenseEditSteps.editing, ExpenseCallback.filter(F.action == 'edit'))
async def process_edit_select(
    callback: CallbackQuery, callback_data: ExpenseCallback, state: FSMContext, session: AsyncSession
):
    await callback.answer()
    expense = await state.get_value('expense')

    match callback_data.value:
        case 'date':
            last_date = expense['date'] + timedelta(1)

            await callback.message.edit_text(
                text=TEXTS['change_date'], reply_markup=get_date_suggestions_kb(last_date=last_date)
            )
            await state.set_state(ExpenseEditSteps.waiting_for_date)
        case 'place':
            await callback.message.edit_text(text=TEXTS['fill_place'])
            await state.set_state(ExpenseEditSteps.waiting_for_place)
        case 'category':
            place_cat_repo = PlaceCategoryRepository(session)
            categories = await place_cat_repo.get_category_by_place(place=expense['place'])
            await callback.message.edit_text(
                text=TEXTS['fill_category'], reply_markup=get_suggestions_kb('select', categories)
            )
            await state.set_state(ExpenseEditSteps.waiting_for_category)
        case 'description':
            await callback.message.edit_text(text=TEXTS['fill_description'])
            await state.set_state(ExpenseEditSteps.waiting_for_description)
        case 'amount':
            pass
        case 'payer':
            pass


@expense_edit_router.message(ExpenseEditSteps.waiting_for_date, F.text)
async def process_date_input(message: Message, state: FSMContext):
    await message.delete()
    try:
        new_date = datetime.strptime(message.text, TEXTS['DATE_FORMAT']).date()
    except ValueError:
        expense = await state.get_value('expense')
        last_date = expense['date'] + timedelta(1)

        await update_step_message(
            message=message,
            state=state,
            text=TEXTS['change_date_incorrect'],
            reply_markup=get_date_suggestions_kb(last_date=last_date),
        )
        return

    await update_expense_data('date', new_date, state)
    await update_expense_message(message, state)
    await update_step_message(message, state, text=TEXTS['edit_text'], reply_markup=get_edit_fields_kb())
    await state.set_state(ExpenseEditSteps.editing)


@expense_edit_router.callback_query(ExpenseEditSteps.waiting_for_date, ExpenseCallback.filter(F.action == 'select'))
async def process_date_select(callback: CallbackQuery, callback_data: ExpenseCallback, state: FSMContext):
    new_date = datetime.strptime(callback_data.value, TEXTS['DATE_FORMAT']).date()
    await update_expense_data('date', new_date, state)
    await update_expense_message(callback.message, state)
    await callback.message.edit_text(text=TEXTS['edit_text'], reply_markup=get_edit_fields_kb())
    await state.set_state(ExpenseEditSteps.editing)


@expense_edit_router.message(ExpenseEditSteps.waiting_for_place, F.text)
async def process_place_input(message: Message, state: FSMContext):
    await message.delete()
    await update_expense_data('place', message.text, state)
    await update_expense_message(message, state)
    await update_step_message(message, state, text=TEXTS['edit_text'], reply_markup=get_edit_fields_kb())
    await state.set_state(ExpenseEditSteps.editing)


@expense_edit_router.message(ExpenseEditSteps.waiting_for_category, F.text)
async def process_category_input(message: Message, state: FSMContext):
    await message.delete()
    await update_expense_data('category', message.text, state)
    await update_expense_message(message, state)
    await update_step_message(message, state, text=TEXTS['edit_text'], reply_markup=get_edit_fields_kb())
    await state.set_state(ExpenseEditSteps.editing)


@expense_edit_router.callback_query(ExpenseEditSteps.waiting_for_category, ExpenseCallback.filter(F.action == 'select'))
async def process_category_select(callback: CallbackQuery, callback_data: ExpenseCallback, state: FSMContext):
    await update_expense_data('category', callback_data.value, state)
    await update_expense_message(callback.message, state)
    await callback.message.edit_text(text=TEXTS['edit_text'], reply_markup=get_edit_fields_kb())
    await state.set_state(ExpenseEditSteps.editing)


@expense_edit_router.message(ExpenseEditSteps.waiting_for_description, F.text)
async def process_description_input(message: Message, state: FSMContext):
    await message.delete()
    await update_expense_data('description', message.text, state)
    await update_expense_message(message, state)
    await update_step_message(message, state, text=TEXTS['edit_text'], reply_markup=get_edit_fields_kb())
    await state.set_state(ExpenseEditSteps.editing)
