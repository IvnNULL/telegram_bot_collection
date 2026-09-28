import logging
from contextlib import suppress

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from handlers.main_menu import send_main_menu
from keyboards.callbacks import ExpenseCallback
from keyboards.keyboards import get_edit_fields_kb
from states.states import ExpenseEditSteps
from texts.texts import TEXTS

logger = logging.getLogger(__name__)

expense_edit_router = Router()


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
