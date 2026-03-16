from aiogram.types import BotCommand
from texts.texts import TEXTS

DEFAULT_COMMANDS = [
    BotCommand(command='/start', description=TEXTS['/start_menu']),
    BotCommand(command='/help', description=TEXTS['/help_menu']),
    BotCommand(command='/add', description=TEXTS['/add_menu']),
    BotCommand(command='/show', description=TEXTS['/show_menu']),
]
