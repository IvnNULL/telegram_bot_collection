import logging

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from database.repositories import ExpenseRepository
from keyboards.keyboards import get_show_menu_kb
from texts.texts import TEXTS

logger = logging.getLogger(__name__)

user_router = Router()


@user_router.message(CommandStart())
async def process_start_command(message: Message, state: FSMContext):
    await message.delete()
    await state.clear()
    await message.answer(text=TEXTS['/start'], reply_markup=get_show_menu_kb())


@user_router.message(Command(commands='clear'))
async def process_clear_command(message: Message, session: AsyncSession):
    expense_repo = ExpenseRepository(session)
    await expense_repo.clear_expenses()
    await message.answer(text=TEXTS['/clear'])


@user_router.message()
async def process_other_message(message: Message):
    await message.delete()
