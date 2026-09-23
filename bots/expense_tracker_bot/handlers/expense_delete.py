import logging

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from database.repositories import ExpenseRepository
from handlers.main_menu import send_main_menu
from keyboards.callbacks import ExpenseCallback
from keyboards.keyboards import get_delete_confirmation_kb
from services.expense_service import expense_dict_to_text
from states.states import ExpenseEditSteps
from texts.texts import TEXTS

logger = logging.getLogger(__name__)

expense_delete_router = Router()


@expense_delete_router.callback_query(
    StateFilter(ExpenseEditSteps.browsing), ExpenseCallback.filter(F.action == 'delete')
)
async def process_delete_click(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await state.set_state(ExpenseEditSteps.deleting)
    await callback.message.edit_reply_markup(reply_markup=get_delete_confirmation_kb())


@expense_delete_router.callback_query(
    StateFilter(ExpenseEditSteps.deleting), ExpenseCallback.filter(F.action == 'confirm')
)
async def process_confirm_click(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    expense = await state.get_value('expense')
    expense_repo = ExpenseRepository(session)
    await expense_repo.delete_expense_by_id(expense['id'])
    await callback.message.edit_text(text=f'{expense_dict_to_text(expense)}\n\n{TEXTS["edit_success_delete"]}')
    await state.clear()
    await send_main_menu(callback.message)
