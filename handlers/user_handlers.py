from datetime import datetime, timedelta
from aiogram import Router, F, Bot
from aiogram.filters import Command, StateFilter
from lexicone import LEXICON_RU, STATE_EXPLAIN
from filters.filters import IsUser, is_float
from aiogram.types import Message, CallbackQuery
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback
from keyboards.inline_kb import categories_inline_kb, create_inline_kb
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from FSM.FSM_states import OldFSM, GetSumFSM
from functions.functions import get_sum, update_base_file, make_xlsx
from time import sleep
from config_data.info import categories_ru, categories
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from functions.chelduler_functions import test_remind1
import asyncio

router = Router()
router.message.filter(IsUser())


@router.message(Command('exit'), ~StateFilter(default_state))
async def process_exit_command(message: Message, state: FSMContext, bot):
    await message.answer(text=LEXICON_RU['as_you_wish'])
    data = await state.get_data()
    first_id = data['first_id']
    sleep(2)
    await bot.delete_messages(chat_id=message.chat.id,
                              message_ids=[id for id in range(first_id, message.message_id + 2)])
    await state.clear()


@router.message(Command('new'), StateFilter(default_state))
async def new_expense_handler(message: Message, state: FSMContext):
    date = datetime.now()
    await state.update_data(input_type='new',
                            date=date.strftime("%-d %B %Y"),
                            text=f'📆 {date.strftime("%-d %B %Y")}',
                            first_id=message.message_id)
    await message.answer(text=f'📆 {date.strftime("%-d %B %Y")}\n\n'
                              f'Выбери категорию 👇🏽',
                         reply_markup=categories_inline_kb)
    await state.set_state(OldFSM.choose_group)


@router.message(Command('old'), StateFilter(default_state))
async def old_expense_handler(message: Message, state: FSMContext):
    calendar = SimpleCalendar(show_alerts=True)
    calendar.set_dates_range(datetime(2022, 11, 1), datetime.now())
    await message.answer(
        text='Расскажи когда это случилось',
        reply_markup=await calendar.start_calendar()
    )
    await state.update_data(input_type='old')
    await state.update_data(first_id=message.message_id)
    await state.set_state(OldFSM.choose_date)


@router.callback_query(SimpleCalendarCallback.filter(), StateFilter(OldFSM.choose_date))
async def calendar_process(callback_query: CallbackQuery, callback_data: SimpleCalendarCallback, state: FSMContext):
    calendar = SimpleCalendar(show_alerts=True)
    calendar.set_dates_range(datetime(2022, 11, 1), datetime.now())
    selected, date = await calendar.process_selection(callback_query, callback_data)
    if selected:
        await state.update_data(date=date.strftime("%-d %B %Y"))
        await state.update_data(text=f'📆 {date.strftime("%-d %B %Y")}')
        await callback_query.message.edit_text(
            text=f'Выбрана дата:\n📆 {date.strftime("%-d %B %Y")}\n\n'
                 f'А теперь на что потратила:',
            reply_markup=categories_inline_kb
        )
        await state.set_state(OldFSM.choose_group)


@router.callback_query(F.data.in_(categories), StateFilter(OldFSM.choose_group))
async def category_process(callback: CallbackQuery, state: FSMContext):
    await state.update_data(category=callback.data)
    data = await state.get_data()
    text = data['text'] + f'\n{LEXICON_RU[callback.data]}'
    await state.update_data(text=text)
    await callback.message.edit_text(text=f"{text}\n\n{LEXICON_RU['input_amount']}")
    await state.set_state(OldFSM.input_amount)


@router.message(is_float, StateFilter(OldFSM.input_amount))
async def process_amount(message: Message, state: FSMContext):
    amount = float(message.text)
    await state.update_data(amount=amount)
    data = await state.get_data()
    text = data['text'] + f"\n🪙 {amount} Лари"
    await state.update_data(text=text)
    await message.answer(
        text=f'Вот что получилось:\n\n{text}',
        reply_markup=create_inline_kb(1, save='Сохранить', comment='Добавить комментарий')
    )
    await state.set_state(OldFSM.save_or_comment)


@router.message(StateFilter(OldFSM.input_amount))
async def process_wrong_amount(message: Message, bot):
    await message.answer(text=LEXICON_RU['wrong_amount'])
    sleep(1.5)
    await bot.delete_messages(chat_id=message.chat.id,
                              message_ids=[message.message_id,
                                           message.message_id + 1])


@router.callback_query(F.data == 'comment', StateFilter(OldFSM.save_or_comment))
async def comment_option_process(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    text = data['text']
    await callback.message.edit_text(text=f'{text}\n\nНапиши любой коммент:')
    await state.set_state(OldFSM.add_comment)


@router.message(F.text, StateFilter(OldFSM.add_comment))
async def process_comment(message: Message, state: FSMContext):
    data = await state.get_data()
    text = data['text'] + f"\n🏷️ {message.text}"
    await state.update_data(text=text)
    await state.update_data(comment=message.text)
    await message.answer(text=text,
                         reply_markup=create_inline_kb(1, save='Сохранить'))
    await state.set_state(OldFSM.save)


@router.callback_query(F.data == 'save', StateFilter(OldFSM.save))
async def save_with_comment(callback: CallbackQuery, state: FSMContext, expense_base, bot: Bot, admin_id):
    index = expense_base[0]['index'] + 1
    expense_base[0]['index'] = index
    await state.update_data(index=index)
    data = await state.get_data()
    text = data['text']
    first_id = data['first_id']
    input_type = data['input_type']
    del data['text']
    del data['first_id']
    expense_base.append(data)
    update_base_file(expense_base)
    await bot.send_message(chat_id=admin_id,
                           text=f"#{index}\n\n{text}")
    if input_type != 'category_button':
        await callback.message.edit_text(text=f"{text}\n\n{LEXICON_RU['done']}",
                                         reply_markup=create_inline_kb(1, more='Есть ещё 👻', done='Пока всё 🫱🏽‍🫲🏾'))
        await bot.delete_messages(chat_id=callback.message.chat.id,
                                  message_ids=[id for id in range(first_id, callback.message.message_id)])
        await state.set_state(OldFSM.more_or_done)

    else:
        await callback.message.edit_text(text=f"{text}\n\n{LEXICON_RU['done']}")
        await bot.delete_messages(chat_id=callback.message.chat.id,
                                  message_ids=[id for id in range(first_id, callback.message.message_id)])
        await state.clear()


@router.callback_query(F.data == 'save', StateFilter(OldFSM.save_or_comment))
async def save_no_comment(callback: CallbackQuery, state: FSMContext, expense_base, bot, admin_id):
    index = expense_base[0]['index'] + 1
    expense_base[0]['index'] = index
    await state.update_data(comment=None,
                            index=index)
    data = await state.get_data()
    text = data['text']
    first_id = data['first_id']
    input_type = data['input_type']
    del data['text']
    del data['first_id']
    expense_base.append(data)
    update_base_file(expense_base)
    await bot.send_message(chat_id=admin_id,
                           text=f"#{index}\n\n{text}")
    if input_type != 'category_button':
        await callback.message.edit_text(text=f"{text}\n\n{LEXICON_RU['done']}",
                                         reply_markup=create_inline_kb(1, more='Есть ещё 👻', done='Пока всё 🫱🏽‍🫲🏾'))
        await bot.delete_messages(chat_id=callback.message.chat.id,
                                  message_ids=[id for id in range(first_id, callback.message.message_id)])
        await state.set_state(OldFSM.more_or_done)
    else:
        await callback.message.edit_text(text=f"{text}\n\n{LEXICON_RU['done']}")
        await bot.delete_messages(chat_id=callback.message.chat.id,
                                  message_ids=[id for id in range(first_id, callback.message.message_id)])
        await state.clear()


@router.callback_query(F.data == 'more', StateFilter(OldFSM.more_or_done))
async def process_one_more(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    input_type = data['input_type']
    if input_type == 'new':
        date = datetime.now()
        await state.update_data(input_type='new',
                                date=date.strftime("%-d %B %Y"),
                                text=f'📆 {date.strftime("%-d %B %Y")}',
                                first_id=callback.message.message_id + 1)
        await callback.message.answer(text=f'📆 {date.strftime("%-d %B %Y")}\n\n'
                                           f'Выбери категорию 👇🏽',
                                      reply_markup=categories_inline_kb)
        await callback.message.delete_reply_markup()
        await state.set_state(OldFSM.choose_group)

    if input_type == 'old':
        calendar = SimpleCalendar(show_alerts=True)
        calendar.set_dates_range(datetime(2022, 11, 1), datetime.now())
        await callback.message.answer(
            text='Расскажи когда это случилось',
            reply_markup=await calendar.start_calendar()
        )
        await state.update_data(input_type='old')
        await state.update_data(first_id=callback.message.message_id + 1)
        await callback.message.delete_reply_markup()
        await state.set_state(OldFSM.choose_date)

    if input_type == 'yesterday':
        date = datetime.now() - timedelta(days=1)
        await state.update_data(input_type='yesterday',
                                date=date.strftime("%-d %B %Y"),
                                text=f'📆 {date.strftime("%-d %B %Y")}',
                                first_id=callback.message.message_id + 1)
        await callback.message.answer(text=f'📆 {date.strftime("%-d %B %Y")}\n\n'
                                           f'Выбери категорию 👇🏽',
                                      reply_markup=categories_inline_kb)
        await callback.message.delete_reply_markup()
        await state.set_state(OldFSM.choose_group)


@router.callback_query(F.data == 'done', StateFilter(OldFSM.more_or_done))
async def process_done(callback: CallbackQuery, state: FSMContext):
    await callback.answer(text='   Спасибо!    \n'
                               'Приходите ещё!',
                          cache_time=3)
    await callback.message.delete_reply_markup()
    await state.clear()


@router.message(F.text.in_(categories_ru), StateFilter(default_state))
async def category_process(message: Message, state: FSMContext):
    first_id = message.message_id
    date = datetime.now().strftime("%-d %B %Y")
    category = categories[categories_ru.index(message.text)]
    text = f"📆 {date}\n{message.text}"
    await state.set_state(OldFSM.input_amount)
    await state.update_data(input_type='category_button',
                            first_id=first_id,
                            date=date,
                            category=category,
                            text=text
                            )
    await message.answer(text=f"{text}\n\nНа сколько мы обеднели?")


@router.message(Command('sum'))
async def process_sum_command(message: Message, state: FSMContext):
    calendar = SimpleCalendar(show_alerts=True)
    calendar.set_dates_range(datetime(2022, 11, 1), datetime.now())
    await message.answer(
        text='Откуда вспоминать?',
        reply_markup=await calendar.start_calendar()
    )
    await state.set_state(GetSumFSM.choose_from)
    await state.update_data(mode='chat')


@router.callback_query(SimpleCalendarCallback.filter(), StateFilter(GetSumFSM.choose_from))
async def process_start_date(callback: CallbackQuery, callback_data: SimpleCalendarCallback, state: FSMContext):
    calendar = SimpleCalendar(show_alerts=True)
    calendar.set_dates_range(datetime(2022, 11, 1), datetime.now())
    selected, date = await calendar.process_selection(callback, callback_data)
    if selected:
        await state.update_data(from_date=date,
                                first_id=callback.message.message_id - 1)
        await callback.message.edit_text(
            text=f'📆 {date.strftime("%-d %B %Y")} - ☁️\n\n'
                 f'А теперь конец периода',
            reply_markup=await calendar.start_calendar()
        )
        await state.set_state(GetSumFSM.choose_to)


@router.callback_query(SimpleCalendarCallback.filter(), StateFilter(GetSumFSM.choose_to))
async def process_end_date(callback: CallbackQuery,
                           callback_data: SimpleCalendarCallback,
                           state: FSMContext,
                           expense_base,
                           bot):
    data = await state.get_data()
    from_date = data['from_date']
    first_id = data['first_id']
    mode = data['mode']
    calendar = SimpleCalendar(show_alerts=True)
    calendar.set_dates_range(from_date, datetime.now())
    selected, date = await calendar.process_selection(callback, callback_data)
    if selected:
        if mode == 'chat':
            decorated_text = get_sum(from_date, date, expense_base)
            if decorated_text:
                await callback.message.edit_text(
                    text=f'📆 {from_date.strftime("%-d %B %Y")} - {date.strftime("%-d %B %Y")}\n\n'
                         f'{decorated_text}',
                    reply_markup=create_inline_kb(1, leave='Оставить в чате', delete='Удалить')
                )
                await bot.delete_message(chat_id=callback.message.chat.id,
                                         message_id=first_id)
                await state.set_state(GetSumFSM.leave_or_delete)

            else:
                await callback.message.edit_text(
                    text=f'📆 {from_date.strftime("%-d %B %Y")} - {date.strftime("%-d %B %Y")}\n\n'
                         f'Там полный ноль по всем пунктам 🙆🏽‍♂️',
                    reply_markup=create_inline_kb(1, delete='Хорошо')
                                                )
                await bot.delete_message(chat_id=callback.message.chat.id,
                                         message_id=first_id)

                await state.set_state(GetSumFSM.leave_or_delete)

        if mode == 'xl':
            file = make_xlsx(from_date, date, expense_base)
            if file:
                await callback.message.answer_document(document=file,
                                                       caption=f'📆 {from_date.strftime("%-d %B %Y")}'
                                                               f' - {date.strftime("%-d %B %Y")}\n')
                await bot.delete_messages(chat_id=callback.message.chat.id,
                                          message_ids=[i for i in range(first_id,
                                                                        callback.message.message_id +1)]
                                                                        )
                await state.clear()

            else:
                await callback.message.edit_text(
                    text=f'📆 {from_date.strftime("%-d %B %Y")} - {date.strftime("%-d %B %Y")}\n\n'
                         f'Там полный ноль по всем пунктам 🙆🏽‍♂️',
                    reply_markup=create_inline_kb(1, delete='Хорошо')
                )
                await bot.delete_message(chat_id=callback.message.chat.id,
                                         message_id=first_id)

                await state.set_state(GetSumFSM.leave_or_delete)


@router.callback_query(F.data == 'leave', StateFilter(GetSumFSM.leave_or_delete))
async def process_leave_choice(callback: CallbackQuery,
                               state: FSMContext):
    await callback.message.edit_text(text=callback.message.text)
    await callback.answer(text='Как скажете 🫡')
    await state.clear()


@router.callback_query(F.data == 'delete', StateFilter(GetSumFSM.leave_or_delete))
async def process_leave_choice(callback: CallbackQuery,
                               state: FSMContext,
                               bot):
    await bot.delete_message(chat_id=callback.message.chat.id,
                             message_id=callback.message.message_id)
    await state.clear()


@router.message(Command('xl'))
async def process_sum_command(message: Message, state: FSMContext):
    calendar = SimpleCalendar(show_alerts=True)
    calendar.set_dates_range(datetime(2022, 11, 1), datetime.now())
    await message.answer(
        text='Откуда вспоминать?',
        reply_markup=await calendar.start_calendar()
    )
    await state.set_state(GetSumFSM.choose_from)
    await state.update_data(mode='xl')


@router.callback_query(F.data == 'ask_decline')
async def process_ask_decline(callback: CallbackQuery, bot):
    await callback.message.edit_text(text='Супер! 😘')
    await asyncio.sleep(2)
    await bot.delete_message(chat_id=callback.message.chat.id,
                             message_id=callback.message.message_id
                             )


@router.callback_query(F.data == 'yesterday_yes')
async def process_yesterday_yes(callback: CallbackQuery, state: FSMContext):
    date = datetime.now() - timedelta(days=1)
    await state.set_state(OldFSM.choose_group)
    await state.update_data(date=date.strftime("%-d %B %Y"),
                            text=f'📆 {date.strftime("%-d %B %Y")}',
                            first_id=callback.message.message_id,
                            input_type='yesterday')
    await callback.message.edit_text(
        text=f'📆 {date.strftime("%-d %B %Y")}\n\n'
             f'Давай вспомним какие:',
        reply_markup=categories_inline_kb
    )


# bellow are handler for answering and deleting any random message
# bellow are handler for answering and deleting any random message
# bellow are handler for answering and deleting any random message
@router.message()
async def process_random_message(message: Message):
    await message.answer(text='Это не то, чего я жду 🥶',
                         reply_markup=create_inline_kb(1,
                                                       understand='🫶🏽 Понятно',
                                                       dont_understand='🤯 Объясни почему'))


@router.callback_query(F.data == 'understand')
async def process_understand_button(callback: CallbackQuery, bot):
    await bot.delete_messages(chat_id=callback.message.chat.id,
                              message_ids=[callback.message.message_id,
                                           callback.message.message_id - 1]
                        )


@router.callback_query(F.data == 'dont_understand', ~StateFilter(default_state))
async def process_dont_understand(callback: CallbackQuery, state: FSMContext, bot):
    status = await state.get_state()
    await callback.message.edit_text(text=STATE_EXPLAIN[status],
                                     reply_markup=create_inline_kb(1, understand='Теперь\nпонятно 🫶'))


@router.callback_query(F.data == 'dont_understand', StateFilter(default_state))
async def process_dont_understand(callback: CallbackQuery, state: FSMContext, bot):
    status = await state.get_state()
    await callback.message.edit_text(text='Честно говоря, я пока понимаю не любые сообщения 😭\n'
                                          'Но зато отлично разбираюсь с командами из меню!',
                                     reply_markup=create_inline_kb(1, understand='Теперь\nпонятно 🫶'))
