import logging

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from database.repositories import ExpenseRepository
from handlers.main_menu import send_main_menu
from services.expense_service import expenses_to_text, expenses_to_csv_text, text_to_csv_file
from texts.texts import TEXTS

logger = logging.getLogger(__name__)

user_router = Router()


@user_router.message(CommandStart())
async def process_start_command(message: Message):
    # await message.answer(text=TEXTS['/start'])
    await send_main_menu(message)


@user_router.message(Command(commands='help'))
async def process_help_command(message: Message):
    await message.answer(text=TEXTS['/help'])


@user_router.message(Command(commands='show'))
async def process_show_command(message: Message, session: AsyncSession):
    expense_repo = ExpenseRepository(session)
    expenses = await expense_repo.list_expenses()
    text = expenses_to_text(expenses) if expenses else TEXTS['no_expenses']
    await message.answer(text=text)


@user_router.message(Command(commands='show_csv'))
async def process_show_csv_command(message: Message, session: AsyncSession):
    expense_repo = ExpenseRepository(session)
    expenses = await expense_repo.list_expenses()

    text = expenses_to_csv_text(expenses) if expenses else TEXTS['no_expenses']
    if len(text) < 4096:
        await message.answer(text=text)
    else:
        csv_file = text_to_csv_file(text)
        await message.answer_document(document=csv_file)


@user_router.message(Command(commands='clear'))
async def process_clear_command(message: Message, session: AsyncSession):
    expense_repo = ExpenseRepository(session)
    await expense_repo.clear_expenses()
    await message.answer(text=TEXTS['/clear'])


@user_router.message()
async def process_other_message(message: Message):
    await message.answer(text=TEXTS['other'])
