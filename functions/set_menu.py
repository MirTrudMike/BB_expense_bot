from lexicone import LEXICON_COMMANDS_RU
from aiogram import Bot
from aiogram.types import BotCommand


async def set_main_menu(bot: Bot):
    menu = [
        BotCommand(
            command=command,
            description=description
        ) for command, description in LEXICON_COMMANDS_RU.items()
    ]
    await bot.set_my_commands(menu)
