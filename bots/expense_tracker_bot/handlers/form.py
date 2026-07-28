import logging
from datetime import date

from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, ReplyMarkupUnion
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from database.repositories import ExpenseRepository, PayerRepository, PlaceCategoryRepository
from keyboards.keyboards import get_save_form_kb, get_payers_kb, get_date_kb, get_kb
from states.states import FSMFillForm
from texts.texts import TEXTS

logger = logging.getLogger(__name__)

form_router = Router()


def get_expense_text(expense_dict: dict) -> str:
    return f'Дата: {expense_dict['date'].strftime('%d.%m.%Y')}\n' \
           f'Место: {expense_dict.get('place', '')}\n' \
           f'Категория: {expense_dict.get('category', '')}\n' \
           f'Описание: {expense_dict.get('description', '')}\n' \
           f'Сумма: {expense_dict.get('amount', '')}\n' \
           f'Плательщик: {expense_dict.get('payer', '')}'


async def update_expense_message(message: Message, state: FSMContext):
    data = await state.get_data()
    expense_text = get_expense_text(data)
    if data.get('expense_message_id'):
        await message.bot.edit_message_text(
            text=expense_text,
            chat_id=message.chat.id,
            message_id=data['expense_message_id']
        )
    else:
        expense_message = await message.answer(expense_text)
        await state.update_data(expense_message_id=expense_message.message_id)


async def update_state_message(message: Message, state: FSMContext, *,
                               text: str, reply_markup: ReplyMarkupUnion | None = None):
    await message.delete()
    data = await state.get_data()
    if data.get('state_message_id'):
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=data['state_message_id'])
        except TelegramBadRequest as e:
            logger.error(e)
    state_message = await message.answer(text=text, reply_markup=reply_markup)
    await state.update_data(state_message_id=state_message.message_id)


@form_router.message(StateFilter(FSMFillForm), Command(commands='cancel'))
@form_router.callback_query(StateFilter(FSMFillForm.save_form), F.data == 'cancel_form')
async def process_cancel_command(event: Message | CallbackQuery, state: FSMContext):
    message = event.message if isinstance(event, CallbackQuery) else event

    data = await state.get_data()
    message_ids = [data.get('start_message_id'), data.get('expense_message_id')]
    for msg_id in message_ids:
        if msg_id:
            try:
                await message.bot.delete_message(chat_id=message.chat.id, message_id=msg_id)
            except TelegramBadRequest as e:
                logger.error(e)

    await update_state_message(message, state, text=TEXTS['cancel_form'], reply_markup=ReplyKeyboardRemove())
    await state.clear()


@form_router.message(StateFilter(default_state), Command(commands='add'))
async def process_add_command(message: Message, state: FSMContext):
    start_message = await message.answer(text=TEXTS['fill_start'])
    await state.update_data(start_message_id=start_message.message_id)
    await state.update_data(date=date.today())
    await update_expense_message(message, state)
    await state.set_state(FSMFillForm.fill_place)

    await update_state_message(message, state, text=TEXTS['fill_place'])


@form_router.message(StateFilter(FSMFillForm.fill_place), F.text)
async def process_place_send(message: Message, state: FSMContext, session_factory: async_sessionmaker[AsyncSession]):
    await state.update_data(place=message.text)
    await update_expense_message(message, state)
    await state.set_state(FSMFillForm.fill_category)

    async with session_factory() as session:
        place_cat_repo = PlaceCategoryRepository(session)
        categories = await place_cat_repo.get_category_by_place(place=message.text)

    if categories is None:
        await update_state_message(message, state, text=TEXTS['fill_category'])
    else:
        await update_state_message(message, state, text=TEXTS['fill_category_with_kb'], reply_markup=get_kb(categories))


@form_router.message(StateFilter(FSMFillForm.fill_category), F.text)
async def process_category_send(message: Message, state: FSMContext):
    await state.update_data(category=message.text)
    await update_expense_message(message, state)
    await state.set_state(FSMFillForm.fill_description)

    await update_state_message(message, state, text=TEXTS['fill_description'], reply_markup=ReplyKeyboardRemove())


@form_router.message(StateFilter(FSMFillForm.fill_description), F.text)
async def process_description_send(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await update_expense_message(message, state)
    await state.set_state(FSMFillForm.fill_amount)

    await update_state_message(message, state, text=TEXTS['fill_amount'])


@form_router.message(StateFilter(FSMFillForm.fill_amount), F.text)
async def process_amount_send(message: Message, state: FSMContext, session_factory: async_sessionmaker[AsyncSession]):
    try:
        amount = int(float(message.text.replace(',', '.').replace(' ', '')))
    except ValueError:
        await update_state_message(message, state, text=TEXTS['fill_amount_error'])
        return

    await state.update_data(amount=amount)
    await update_expense_message(message, state)
    await state.set_state(FSMFillForm.fill_payer)

    async with session_factory() as session:
        payer_repo = PayerRepository(session)
        payers = await payer_repo.list_payers()

    if payers is None:
        await update_state_message(message, state, text=TEXTS['fill_payer'])
    else:
        await update_state_message(message, state, text=TEXTS['fill_payer'], reply_markup=get_payers_kb(payers))


@form_router.message(StateFilter(FSMFillForm.fill_payer), F.text)
async def process_payer_send(message: Message, state: FSMContext):
    await state.update_data(payer=message.text)
    await update_expense_message(message, state)
    await state.set_state(FSMFillForm.save_form)
    await update_state_message(message, state, text=TEXTS['check_form'], reply_markup=get_save_form_kb())


@form_router.callback_query(StateFilter(FSMFillForm.save_form), F.data == 'change_date_form')
async def process_change_date_click(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FSMFillForm.change_date)
    await update_state_message(callback.message, state, text=TEXTS['change_date'], reply_markup=get_date_kb('%d.%m.%Y'))


@form_router.message(StateFilter(FSMFillForm.change_date), F.text)
async def process_change_date_send(message: Message, state: FSMContext):
    try:
        day, month, year = [int(n) for n in message.text.split('.')]
        new_date = date(year, month, day)
    except ValueError:
        await update_state_message(message, state, text=TEXTS['change_date'])
        return

    await state.update_data(date=new_date)
    await update_expense_message(message, state)
    await state.set_state(FSMFillForm.save_form)

    await update_state_message(message, state, text=TEXTS['check_form'], reply_markup=get_save_form_kb())


@form_router.callback_query(StateFilter(FSMFillForm.save_form), F.data == 'save_form')
async def process_save_form_click(callback: CallbackQuery, state: FSMContext,
                                  session_factory: async_sessionmaker[AsyncSession]):
    async with session_factory() as session:
        data = await state.get_data()
        expense_repo = ExpenseRepository(session)
        payer_repo = PayerRepository(session)
        place_cat_repo = PlaceCategoryRepository(session)

        await expense_repo.add_expense(
            user_id=callback.from_user.id,
            exp_date=data['date'],
            category=data['category'],
            place=data['place'],
            description=data['description'],
            amount=data['amount'],
            payer=data['payer']
        )
        await payer_repo.add_payer(payer=data['payer'])
        await place_cat_repo.add_place_category(place=data['place'], category=data['category'])

    await callback.message.edit_text(text=TEXTS['save_form'])
    await state.clear()


@form_router.message(StateFilter(FSMFillForm))
async def process_wrong_send(message: Message):
    # await message.answer(text=TEXTS['fill_wrong'])
    await message.delete()
