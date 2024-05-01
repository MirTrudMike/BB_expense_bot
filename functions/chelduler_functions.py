from aiogram.types import Message
from aiogram import Bot
from keyboards.inline_kb import create_inline_kb
from apscheduler.schedulers.asyncio import AsyncIOScheduler


async def test_remind1(message: Message):
    await message.answer(text='TEST   1')


async def ask_yesterday(bot: Bot, user_id: int):
    await bot.send_message(chat_id=user_id,
                           text='  ☀️ Доброе утро ☀️\n\n'
                                'Были ли вчера расходы?',
                           reply_markup=create_inline_kb(width=1,
                                                         yesterday_yes='Были 😢',
                                                         ask_decline='Не было 😎'))


async def ask_new_month_worksheet(bot: Bot, user_id: int):
    await bot.send_message(chat_id=user_id,
                           text='😱 Кстати, начался новый месяц\n\n'
                                '📄 Я могу сделать новый лист в სალარო',
                           reply_markup=create_inline_kb(width=1,
                                                         new_worksheet_yes='Сделай 🙏🏼',
                                                         ask_decline='Я сама 🧔🏼‍♀️'))


def set_schedulers(bot: Bot, user_ids: list, scheduler: AsyncIOScheduler):
    for user in user_ids:
        try:
            scheduler.add_job(ask_yesterday,
                              trigger='cron',
                              hour="10",
                              minute="30",
                              kwargs={'bot': bot,
                                      'user_id': user}
                          )
            scheduler.add_job(ask_new_month_worksheet,
                              trigger='cron',
                              day="1",
                              hour="15",
                              minute="30",
                              kwargs={'bot': bot,
                                      'user_id': user}
                              )

        except: pass
