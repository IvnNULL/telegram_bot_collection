from datetime import date, timedelta

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from keyboards.callbacks import ExpenseCallback
from texts.texts import TEXTS


def get_suggestions_kb(action: str, values: list[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for value in values:
        builder.button(text=value, callback_data=ExpenseCallback(action=action, value=value).pack())
    builder.adjust(3)
    return builder.as_markup()


def get_date_suggestions_kb(last_date: date, days: int = 3) -> InlineKeyboardMarkup:
    dates = [(last_date - timedelta(i)).strftime('%d.%m.%Y') for i in range(days - 1, -1, -1)]
    return get_suggestions_kb(action='select', values=dates)


def get_add_confirmation_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=TEXTS['save_button'], callback_data=ExpenseCallback(action='save').pack()),
        InlineKeyboardButton(text=TEXTS['cancel_button'], callback_data=ExpenseCallback(action='cancel').pack()),
    )
    builder.row(
        InlineKeyboardButton(
            text=TEXTS['change_date_button'], callback_data=ExpenseCallback(action='change', value='date').pack()
        )
    )
    return builder.as_markup()


def get_date_keyboard(start_date: date, days: int = 3, prefix: str = '') -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    button_date = start_date - timedelta(days=1)
    for _ in range(days):
        button_date += timedelta(days=1)
        button_date_text = button_date.strftime(TEXTS['DATE_FORMAT'])
        builder.add(InlineKeyboardButton(text=button_date_text, callback_data=f'{prefix}{button_date_text}'))
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


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.button(text=TEXTS['main_menu:expense:add'], callback_data='expense:add')
    builder.button(text=TEXTS['main_menu:expense:edit'], callback_data='expense:edit')
    # builder.button(text=TEXTS['main_menu:expense:show'], callback_data='expense:show')

    builder.adjust(1)
    return builder.as_markup()
