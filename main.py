import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
#....
from config_data.config import Config, load_config


config: Config = load_config('.env')

bot = Bot(token=config.tg_bot.token)
dp = Dispatcher()




async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())