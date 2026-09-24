from aiogram.types import BotCommand
from texts.texts import TEXTS

DEFAULT_COMMANDS = [
    BotCommand(command='/start', description=TEXTS['/start_description']),
]
