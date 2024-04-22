import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config_data.config import Config, load_config

from handlers import unknow_user_handlers, user_handlers

config: Config = load_config('.env')

storage = MemoryStorage()

bot = Bot(token=config.tg_bot.token)
dp = Dispatcher(storage=storage)
dp.workflow_data.update(
    {
        'password': config.tg_bot.password,
        'user_ids': config.tg_bot.user_ids,
        'admin_ids': config.tg_bot.admin_ids,
        'expense_base': config.expense_base
    }
)

dp.include_router(unknow_user_handlers.router)
dp.include_router(user_handlers.router)


async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
