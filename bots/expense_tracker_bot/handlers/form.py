import logging
from datetime import date

from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from database.db import add_expense, add_payer, list_payers
from keyboards.keyboards import get_save_form_kb, get_payers_kb
from states.states import FSMFillForm
from texts.texts import TEXTS

logger = logging.getLogger(__name__)

form_router = Router()


@form_router.message(Command(commands='add'), StateFilter(default_state))
async def process_add_command(message: Message, state: FSMContext):
    await message.answer(text=TEXTS['fill_start'])
    await state.set_state(FSMFillForm.fill_category)
    await state.update_data(date=date.today())
    await message.answer(text=TEXTS['fill_category'])


@form_router.message(StateFilter(FSMFillForm), Command(commands='cancel'))
async def process_category_send(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(text=TEXTS['cancel_form'], reply_markup=ReplyKeyboardRemove())


@form_router.message(StateFilter(FSMFillForm.fill_category), F.text)
async def process_category_send(message: Message, state: FSMContext):
    await state.update_data(category=message.text)
    await state.set_state(FSMFillForm.fill_place)
    await message.answer(text=TEXTS['fill_place'])


@form_router.message(StateFilter(FSMFillForm.fill_place), F.text)
async def process_place_send(message: Message, state: FSMContext):
    await state.update_data(place=message.text)
    await state.set_state(FSMFillForm.fill_description)
    await message.answer(text=TEXTS['fill_description'])


@form_router.message(StateFilter(FSMFillForm.fill_description), F.text)
async def process_description_send(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(FSMFillForm.fill_amount)
    await message.answer(text=TEXTS['fill_amount'])


@form_router.message(StateFilter(FSMFillForm.fill_amount), F.text)
async def process_amount_send(message: Message, state: FSMContext, session_factory: async_sessionmaker[AsyncSession]):
    try:
        amount = int(message.text.replace(',', '.').replace(' ', ''))
    except ValueError:
        await message.answer(TEXTS['fill_amount_error'])
        return

    await state.update_data(amount=amount)
    await state.set_state(FSMFillForm.fill_payer)
    async with session_factory() as session:
        payers = await list_payers(session)
    await message.answer(text=TEXTS['fill_payer'], reply_markup=get_payers_kb(payers))


@form_router.message(StateFilter(FSMFillForm.fill_payer), F.text)
async def process_payer_send(message: Message, state: FSMContext):
    await state.update_data(payer=message.text)

    await message.answer(
        text=TEXTS['check_form'],
        reply_markup=ReplyKeyboardRemove()
    )

    data = await state.get_data()
    await message.answer(
        text=f'Дата: {data['date']}\n'
             f'Категория: {data['category']}\n'
             f'Место: {data['place']}\n'
             f'Описание: {data['description']}\n'
             f'Сумма: {data['amount']}\n'
             f'Плательщик: {data['payer']}',
        reply_markup=get_save_form_kb()
    )

    await state.set_state(FSMFillForm.save_form)


@form_router.callback_query(StateFilter(FSMFillForm.save_form), F.data.in_(['save_form', 'cancel_form']))
async def process_save_form(callback: CallbackQuery, state: FSMContext,
                            session_factory: async_sessionmaker[AsyncSession]):
    await callback.message.edit_reply_markup()
    if callback.data == 'save_form':
        async with session_factory() as session:
            data = await state.get_data()
            await add_expense(
                session,
                user_id=callback.from_user.id,
                exp_date=data['date'],
                category=data['category'],
                place=data['place'],
                description=data['description'],
                amount=data['amount'],
                payer=data['payer']
            )
            await add_payer(session, payer=data['payer'])
        await callback.message.answer(text=TEXTS['save_form'])
    else:
        await callback.message.edit_text(text=TEXTS['cancel_form'])
    await state.clear()


@form_router.message(StateFilter(FSMFillForm))
async def process_wrong_send(message: Message):
    await message.answer(text=TEXTS['fill_wrong'])
