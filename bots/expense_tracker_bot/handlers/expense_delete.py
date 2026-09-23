import logging

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from database.repositories import ExpenseRepository
from handlers.main_menu import send_main_menu
from keyboards.callbacks import ExpenseCallback
from states.states import ExpenseEditSteps
from texts.texts import TEXTS

logger = logging.getLogger(__name__)

expense_delete_router = Router()


@expense_delete_router.callback_query(
    StateFilter(ExpenseEditSteps.browsing), ExpenseCallback.filter(F.action == 'delete')
)
async def process_delete_click(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    expense = await state.get_value('expense')
    expense_repo = ExpenseRepository(session)
    await expense_repo.delete_expense_by_id(expense['id'])
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(text=TEXTS['edit_success_delete'])
    await state.clear()
    await send_main_menu(callback.message)
