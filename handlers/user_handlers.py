from datetime import datetime
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from lexicone import LEXICON_RU
from filters.filters import IsUser, is_float
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, CallbackQuery
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback, get_user_locale
from keyboards.inline_kb import categories_inline_kb, create_inline_kb
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from FSM.user_FSM import OldFSM
from functions.functions import decorate_expense, update_base_file
from aiogram.methods.delete_messages import DeleteMessages
from time import sleep

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
    await state.update_data(type='new',
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
    await state.update_data(type='old')
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


# Not really needed
@router.message(StateFilter(OldFSM.choose_date))
async def expect_date_warning(message: Message):
    await message.answer(text=LEXICON_RU['date_expected_warning'])


@router.callback_query(StateFilter(OldFSM.choose_group))
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
    await state.set_state(OldFSM.saveorcomment)



@router.message(StateFilter(OldFSM.input_amount))
async def process_wrong_amount(message: Message, bot):
    await message.answer(text=LEXICON_RU['wrong_amount'])
    sleep(1.5)
    await bot.delete_messages(chat_id=message.chat.id,
                              message_ids=[message.message_id,
                                           message.message_id + 1])


@router.callback_query(F.data == 'comment', StateFilter(OldFSM.saveorcomment))
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
async def save_with_comment(callback: CallbackQuery, state: FSMContext, expense_base, bot):
    data = await state.get_data()
    text = data['text']
    first_id = data['first_id']
    await callback.message.edit_text(text=f"{text}\n\n{LEXICON_RU['done']}")
    del data['text']
    del data['first_id']
    expense_base.append(data)
    update_base_file(expense_base)
    await state.clear()
    await bot.delete_messages(chat_id=callback.message.chat.id,
                              message_ids=[id for id in range(first_id, callback.message.message_id)])


@router.callback_query(F.data == 'save', StateFilter(OldFSM.saveorcomment))
async def save_no_comment(callback: CallbackQuery, state: FSMContext, expense_base, bot):
    await state.update_data(comment=None)
    data = await state.get_data()
    text = data['text']
    first_id = data['first_id']
    await callback.message.edit_text(text=f"{text}\n\n{LEXICON_RU['done']}")
    del data['text']
    del data['first_id']
    expense_base.append(data)
    update_base_file(expense_base)
    await state.clear()
    await bot.delete_messages(chat_id=callback.message.chat.id,
                              message_ids=[id for id in range(first_id, callback.message.message_id)])






