from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from texts.texts import TEXTS


def get_save_form_kb():
    save_button = InlineKeyboardButton(text=TEXTS['save_button'], callback_data='save_form')
    cancel_button = InlineKeyboardButton(text=TEXTS['cancel_button'], callback_data='cancel_form')

    keyboard: list[list[InlineKeyboardButton]] = [[save_button, cancel_button]]

    return InlineKeyboardMarkup(inline_keyboard=keyboard)
