from environs import Env
from dataclasses import dataclass


@dataclass
class TgBot:
    token: str


@dataclass()
class LogSettings:
    level: str
    format: str


@dataclass()
class Config:
    bot: TgBot
    log: LogSettings


def load_config() -> Config:
    env = Env()
    env.read_env()

    return Config(
        bot=TgBot(token=env('BOT_TOKEN')),
        log=LogSettings(level=env('LOG_LEVEL'), format=env('LOG_FORMAT'))
    )
