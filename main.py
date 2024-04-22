import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from middleware.apschadulermiddleware import SchedulerMiddleware
from aiogram.fsm.storage.memory import MemoryStorage
from config_data.config import Config, load_config
from handlers import unknow_user_handlers, user_handlers
from functions.chelduler_functions import set_schedulers
from keyboards.regular_kb import reg_categories_kb


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


@dp.message(Command('start'))
async def open_kd(message: Message):
    await message.answer(text='Vot:',
                         reply_markup=reg_categories_kb.as_markup())

dp.include_router(unknow_user_handlers.router)
dp.include_router(user_handlers.router)


async def main() -> None:
    # And the run events dispatching
    scheduler = AsyncIOScheduler()

    dp.update.middleware(
        SchedulerMiddleware(scheduler=scheduler),
    )

    set_schedulers(bot, config.tg_bot.user_ids[1:], scheduler)

    scheduler.start()
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())

