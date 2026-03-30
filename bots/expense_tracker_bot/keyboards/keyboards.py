from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from database.models import Payer
from texts.texts import TEXTS


def get_save_form_kb():
    save_button = InlineKeyboardButton(text=TEXTS['save_button'], callback_data='save_form')
    cancel_button = InlineKeyboardButton(text=TEXTS['cancel_button'], callback_data='cancel_form')

    keyboard: list[list[InlineKeyboardButton]] = [[save_button, cancel_button]]

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_payers_kb(payers: list[Payer]) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    for payer in payers:
        builder.add(KeyboardButton(text=payer.payer))
    builder.adjust(3)

    return builder.as_markup(resize_keyboard=True)
