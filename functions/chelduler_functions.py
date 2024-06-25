from aiogram.types import Message
from aiogram import Bot
from keyboards.inline_kb import create_inline_kb
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from breakfast.bf_functions import make_breakfast_plan_for_day, get_cook_counter
from datetime import datetime
import asyncio


async def test_remind1(message: Message):
    await message.answer(text='TEST   1')


async def ask_yesterday(bot: Bot, user_ids: list):
    for user_id in user_ids:
        await bot.send_message(chat_id=user_id,
                               text='  ☀️ Доброе утро ☀️\n\n'
                                    'Были ли вчера расходы?',
                               reply_markup=create_inline_kb(width=1,
                                                             yesterday_yes='Были 😢',
                                                             ask_decline='Не было 😎'))


async def ask_new_month_worksheet(bot: Bot, user_ids: list):
    for user_id in user_ids:
        await bot.send_message(chat_id=user_id,
                               text='😱 Кстати, начался новый месяц\n\n'
                                    '📄 Я могу сделать новый лист в სალარო',
                               reply_markup=create_inline_kb(width=1,
                                                             new_worksheet_yes='Сделай 🙏🏼',
                                                             ask_decline='Я сама 🧔🏼‍♀️'))


async def ask_breakfast(bot: Bot, user_ids: list, bnovo_login, bnovo_password, admin_id):
    response = False
    while not response:
        response = make_breakfast_plan_for_day(datetime.now(), bnovo_login, bnovo_password)
        total_bf = response[0]
        text = response[1]
        date_text = datetime.now().strftime('%d.%m.%Y')
        if total_bf != 0:
            for user_id in user_ids:
                await bot.send_message(chat_id=user_id,
                                       text=f"📆 {date_text}\n"
                                            f"🫡 Вот что я узнал про завтраки!\n\n"
                                            f"Сегодня было так:\n"
                                            f"{text}\n\n"
                                            f"🥯 Всего завтраков: {total_bf}",
                                       reply_markup=create_inline_kb(1,
                                                                     bf_count_correct="✅ Правильно",
                                                                     bf_count_wrong="❌ Нет, не так!"))
                await bot.send_message(chat_id=admin_id,
                                       text=f"📆 {date_text}\n"
                                            f"❓ Breakfast Asked")
        else:
            for user_id in user_ids:
                await bot.send_message(chat_id=user_id,
                                       text=f"📆 {date_text}\n"
                                            f"Я там проверил, и кажется\n\n"
                                            f"🥯 Сегодня не было завтраков?",
                                       reply_markup=create_inline_kb(1,
                                                                     no_bf_correct="✅ Правильно",
                                                                     bf_count_wrong="❌ Нет, не так!")
                                       )
                await bot.send_message(chat_id=admin_id,
                                       text=f"📆 {date_text}\n"
                                            f"❓ Breakfast Asked")

        await asyncio.sleep(600)


def set_schedulers(bot: Bot, user_ids: list, scheduler: AsyncIOScheduler, bnovo_login, bnovo_password, admin_id: int):
    scheduler.add_job(ask_yesterday,
                      trigger='cron',
                      hour="8",
                      minute="10",
                      kwargs={'bot': bot,
                              'user_ids': user_ids}
                      )
    scheduler.add_job(ask_new_month_worksheet,
                      trigger='cron',
                      day="1",
                      hour="12",
                      minute="1",
                      kwargs={'bot': bot,
                              'user_ids': user_ids}
                      )
    scheduler.add_job(ask_breakfast,
                      trigger='cron',
                      hour="23",
                      minute="5",
                      kwargs={'bot': bot,
                              'user_ids': user_ids,
                              'bnovo_login': bnovo_login,
                              'bnovo_password': bnovo_password,
                              'admin_id': admin_id}
                      )
