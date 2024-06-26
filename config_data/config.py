from dataclasses import dataclass
from environs import Env
import json


def load_base():
    with open('expense_base.json', mode='r') as file:
        base = json.load(file)
        return base


@dataclass
class TgBot:
    token: str
    user_ids: list[int]
    admin_ids: list[int]
    blocked_ids: list[int]
    password: str

@dataclass
class Bnovo:
    login: str
    password: str

@dataclass
class Config:
    tg_bot: TgBot
    bnovo: Bnovo


def load_config(path):
    env = Env()
    env.read_env(path)

    return Config(
        tg_bot=TgBot(
            token=env('BOT_TOKEN'),
            admin_ids=list(map(int, env.list('ADMIN_IDS'))),
            user_ids=list(map(int, env.list('USER_IDS'))),
            blocked_ids=list(map(int, env.list('BLOCKED_IDS'))),
            password=env('PASSWORD')),
        bnovo=Bnovo(
            login=env('BNOVO_LOGIN'),
            password=env('BNOVO_PASSWORD'))
    )
