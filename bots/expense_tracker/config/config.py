from dataclasses import dataclass
from environs import Env


@dataclass
class TgBot:
    token: str
    allow_ids: list[int]


@dataclass()
class LogSettings:
    level: str
    format: str


@dataclass()
class DatabaseSettings:
    url: str


@dataclass()
class Config:
    bot: TgBot
    log: LogSettings
    db: DatabaseSettings


def load_config() -> Config:
    env = Env()
    env.read_env()

    raw_ids = env.list('ALLOW_IDS', default=[])

    try:
        allow_ids = [int(n) for n in raw_ids]
    except ValueError as e:
        raise ValueError(f'ALLOW_IDS must be integers, got: {raw_ids}') from e

    return Config(
        bot=TgBot(token=env('BOT_TOKEN'), allow_ids=allow_ids),
        log=LogSettings(level=env('LOG_LEVEL'), format=env('LOG_FORMAT')),
        db=DatabaseSettings(url=env('DATABASE_URL')),
    )
