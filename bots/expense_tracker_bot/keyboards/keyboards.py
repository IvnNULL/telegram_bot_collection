from datetime import date, timedelta

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from keyboards.callbacks import ExpenseCallback, MenuCallback
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


def get_add_shortcut_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=TEXTS['main_menu:expense:add'], callback_data=MenuCallback(target='expense_add').pack())
    builder.button(text=TEXTS['main_menu:menu'], callback_data=MenuCallback(target='main').pack())
    builder.adjust(2)
    return builder.as_markup()


def get_delete_confirmation_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=TEXTS['confirm_deletion_button'], callback_data=ExpenseCallback(action='confirm').pack())
    builder.button(text=TEXTS['cancel_button'], callback_data=ExpenseCallback(action='cancel').pack())
    builder.adjust(1)
    return builder.as_markup()


def get_browsing_kb(
    expense_buttons: list[dict], current_page: int, total_pages: int, current_date: date
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for button in expense_buttons:
        builder.row(
            InlineKeyboardButton(
                text=button['text'], callback_data=ExpenseCallback(action='select', value=button['index']).pack()
            )
        )

    builder.row(
        InlineKeyboardButton(
            text=current_date.strftime(TEXTS['DATE_FORMAT']),
            callback_data=ExpenseCallback(action='change', value='date').pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(text='<', callback_data=ExpenseCallback(action='move', value='-1').pack()),
        InlineKeyboardButton(text=f'{current_page}/{total_pages}', callback_data=ExpenseCallback(action='pass').pack()),
        InlineKeyboardButton(text='>', callback_data=ExpenseCallback(action='move', value='+1').pack()),
    )
    builder.row(
        InlineKeyboardButton(text=TEXTS['cancel_button'], callback_data=ExpenseCallback(action='cancel').pack())
    )
    return builder.as_markup()


def get_action_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text=TEXTS['delete_button'], callback_data=ExpenseCallback(action='delete').pack())
    builder.button(text=TEXTS['return_button'], callback_data=ExpenseCallback(action='return').pack())
    return builder.as_markup()


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.button(text=TEXTS['main_menu:expense:add'], callback_data=MenuCallback(target='expense_add').pack())
    builder.button(text=TEXTS['main_menu:expense:edit'], callback_data=MenuCallback(target='expense_edit').pack())
    # builder.button(text=TEXTS['main_menu:expense:show'], callback_data='expense:show')

    builder.adjust(1)
    return builder.as_markup()
