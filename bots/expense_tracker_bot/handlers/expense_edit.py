import logging

from aiogram import Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import Message
from states.states import FSMEditExpense
from texts.texts import TEXTS

logger = logging.getLogger(__name__)

edit_router = Router()


@edit_router.message(StateFilter(default_state), Command(commands='edit'))
async def process_edit_command(message: Message, state: FSMContext):
    await message.delete()
    await state.set_state(FSMEditExpense.browsing)
    edit_message = await message.answer(text=TEXTS['edit_start'])
    await state.update_data(edit_message_id=edit_message.message_id)


@edit_router.message(StateFilter(FSMEditExpense), Command('cancel'))
async def process_cancel_command(message: Message, state: FSMContext):
    await message.delete()
    edit_message_id = await state.get_value('edit_message_id')
    try:
        await message.bot.delete_message(chat_id=message.chat.id, message_id=edit_message_id)
    except TelegramBadRequest as e:
        logger.error(e)
    await state.clear()
