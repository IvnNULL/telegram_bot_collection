from datetime import date, timedelta

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from database.models import Payer
from texts.texts import TEXTS


def get_save_form_kb() -> InlineKeyboardMarkup:
    change_date_button = InlineKeyboardButton(text=TEXTS['change_date_button'], callback_data='change_date_form')
    save_button = InlineKeyboardButton(text=TEXTS['save_button'], callback_data='save_form')
    cancel_button = InlineKeyboardButton(text=TEXTS['cancel_button'], callback_data='cancel_form')

    keyboard = [
        [change_date_button],
        [save_button, cancel_button]
    ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_payers_kb(payers: list[Payer]) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    for payer in payers:
        builder.add(KeyboardButton(text=payer.payer))
    builder.adjust(3)

    return builder.as_markup(resize_keyboard=True)


def get_date_kb(format_date: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[
            KeyboardButton(text=(date.today() - timedelta(days=2)).strftime(format_date)),
            KeyboardButton(text=(date.today() - timedelta(days=1)).strftime(format_date)),
            KeyboardButton(text=date.today().strftime(format_date)),
        ]],
        resize_keyboard=True
    )
