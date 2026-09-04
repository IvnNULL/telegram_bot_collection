from datetime import date, timedelta

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from texts.texts import TEXTS


def get_save_form_keyboard() -> InlineKeyboardMarkup:
    change_date_button = InlineKeyboardButton(text=TEXTS['change_date_button'], callback_data='change_date_form')
    save_button = InlineKeyboardButton(text=TEXTS['save_button'], callback_data='save_form')
    cancel_button = InlineKeyboardButton(text=TEXTS['cancel_button'], callback_data='cancel_form')
    keyboard = [
        [save_button, cancel_button],
        [change_date_button],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def create_inline_keyboard(texts: list[str], data_prefix: str, adjust: int = 3) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for text in texts:
        builder.button(text=text, callback_data=f'{data_prefix}{text}')
    builder.adjust(adjust)
    return builder.as_markup()


def get_date_inline_keyboard(format_date: str, data_prefix: str, days: int = 3) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    current_date = date.today() - timedelta(days=days - 1)
    for _ in range(days):
        text_date = current_date.strftime(format_date)
        builder.button(text=text_date, callback_data=f'{data_prefix}{text_date}')
        current_date += timedelta(days=1)
    builder.adjust(3)
    return builder.as_markup()


def get_expenses_keyboard(
    expense_buttons: list[dict], current_page: int, total_pages: int, current_date: date
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for button in expense_buttons:
        builder.row(InlineKeyboardButton(text=button['text'], callback_data=f'select:{button["index"]}'))

    builder.row(InlineKeyboardButton(text=current_date.strftime(TEXTS['DATE_FORMAT']), callback_data='change_date'))
    builder.row(
        InlineKeyboardButton(text='<', callback_data='move:-1'),
        InlineKeyboardButton(text=f'{current_page}/{total_pages}', callback_data='pass'),
        InlineKeyboardButton(text='>', callback_data='move:+1'),
    )
    builder.row(InlineKeyboardButton(text=TEXTS['cancel_button'], callback_data='cancel'))
    return builder.as_markup()
