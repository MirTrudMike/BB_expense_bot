from datetime import datetime
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from lexicone import LEXICON_RU
from filters.filters import IsUser, is_float
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, CallbackQuery
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback, get_user_locale
from aiogram.filters.callback_data import CallbackData
from keyboards.inline_kb import categories_inline_kb, create_inline_kb
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from FSM.user_FSM import OldFSM
from functions.functions import decorate_expense

router = Router()
router.message.filter(IsUser())


@router.message(Command('exit'), ~StateFilter(default_state))
async def process_exit_command(message: Message, state: FSMContext):
    await message.answer(text=LEXICON_RU['as_you_wish'])
    await state.clear()


@router.message(Command('old'), StateFilter(default_state))
async def old_expense_handler(message: Message, state: FSMContext):
    calendar = SimpleCalendar(show_alerts=True)
    calendar.set_dates_range(datetime(2022, 11, 1), datetime.now())
    await message.answer(
        text='Расскажи когда это случилось',
        reply_markup=await calendar.start_calendar()
    )
    await state.set_state(OldFSM.choose_date)


@router.callback_query(SimpleCalendarCallback.filter(), StateFilter(OldFSM.choose_date))
async def calendar_process(callback_query: CallbackQuery, callback_data: SimpleCalendarCallback, state: FSMContext):
    calendar = SimpleCalendar(show_alerts=True)
    selected, date = await calendar.process_selection(callback_query, callback_data)
    if selected:
        await state.update_data(date=date)
        await callback_query.message.edit_text(
            text=f'Выбрана дата: {date.strftime("%d-%m-%Y")}\n\n'
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
    await callback.message.edit_text(text=LEXICON_RU['input_amount'])
    await state.set_state(OldFSM.input_amount)


@router.message(is_float, StateFilter(OldFSM.input_amount))
async def process_amount(message: Message, state: FSMContext):
    amount = float(message.text)
    await state.update_data(amount=amount)
    data = await state.get_data()
    await message.answer(
        text=f'Вот что получилось:\n\n{decorate_expense(data)}',
        reply_markup=create_inline_kb(1, save='Сохранить', comment='Добавить комментарий')
    )


@router.message(StateFilter(OldFSM.input_amount))
async def process_wrong_amount(message: Message):
    await message.answer(text=LEXICON_RU['wrong_amount'])





