from aiogram import Router, Bot
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery
from filters.filters import IsAdmin, is_int
from aiogram import F
from functions.functions import decorate_expense
from functions.functions import find_expense_index_in_base, delete_record_by_base_index
from functions.functions import load_base, restore_base, get_base_to_tg, get_sum, make_xlsx
from functions.gs_functions import create_new_month_worksheet
from FSM.FSM_states import AdminFSM, AdminGetSumFSM
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from keyboards.inline_kb import create_inline_kb
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback
from datetime import datetime
from breakfast.bf_functions import make_breakfast_plan_for_day

router = Router()
router.message.filter(IsAdmin())


@router.message(Command('test', prefix='.'))
async def do_test(message: Message, bnovo_login, bnovo_password):
    plan = make_breakfast_plan_for_day(datetime.now(), bnovo_login, bnovo_password)
    if plan:
        await message.answer(text=f"Всего Завтраков: {plan[0]}\n"
                                  f"{plan[1]}")
    else:
        await message.answer(text='НИХУЯ')


@router.callback_query(F.data == 'exit', ~StateFilter(default_state))
async def process_exit(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    first_id = data['first_id']
    await bot.delete_messages(chat_id=callback.message.chat.id,
                              message_ids=[i for i in range(first_id,
                                                            callback.message.message_id + 1)]
                              )
    await state.clear()


@router.message(Command('del', prefix='..'))
async def delete_command_handler(message: Message, state: FSMContext):
    await message.answer(text="Input record INDEX:")
    await state.set_state(AdminFSM.input_index)
    await state.update_data(first_id=message.message_id)


@router.message(is_int, StateFilter(AdminFSM.input_index))
async def process_index(message: Message, state: FSMContext):
    index = int(message.text)
    base = load_base()
    try:
        base_index = find_expense_index_in_base(index)

        await state.update_data(index=index,
                                base_index=base_index)
        await message.answer(text=f"Index: {index}\n\n"
                                  f"{decorate_expense(base[base_index])}",
                             reply_markup=create_inline_kb(1,
                                                           confirm_del="Confirm ✅",
                                                           exit="NO ⛔"))
        await state.set_state(AdminFSM.confirm_del)

    except:
        await message.answer(text='No element in BASE',
                             reply_markup=create_inline_kb(1, exit='OK'))


@router.callback_query(F.data == 'confirm_del', StateFilter(AdminFSM.confirm_del))
async def process_del_record(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    index = data['index']
    base_index = data['base_index']
    delete_record_by_base_index(base_index)
    await callback.message.edit_text(text=f"Deleted record #{index}\n\nDONE ✅")
    await state.clear()


@router.message(Command('restore_base', prefix='.'))
async def process_restore_base_command(message: Message, state: FSMContext):
    await message.answer(text="⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️\n"
                              "!!!!!!!!WARNING!!!!!!!\n"
                              "Delete the whole BASE?\n"
                              "⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️",
                         reply_markup=create_inline_kb(1,
                                                       confirm_restore_base="Confirm ✅",
                                                       exit="NO ⛔"))
    await state.set_state(AdminFSM.confirm_restore_base)
    await state.update_data(first_id=message.message_id)


@router.callback_query(F.data == 'confirm_restore_base', StateFilter(AdminFSM.confirm_restore_base))
async def process_restore_base_confirm(callback: CallbackQuery, state: FSMContext, bot: Bot):
    restore_base()
    data = await state.get_data()
    first_id = data['first_id']
    await callback.message.edit_text(text='⚠️BASE RESTORED⚠️')
    await bot.delete_message(chat_id=callback.message.chat.id,
                             message_id=first_id)
    await state.clear()


@router.message(Command('get_base_json', prefix='.'))
async def process_get_json(message: Message, bot: Bot):
    file = get_base_to_tg()
    await message.answer_document(document=file,
                                  caption='Full base at the moment')
    await bot.delete_message(chat_id=message.chat.id,
                             message_id=message.message_id)


@router.message(Command('sum', prefix='.'))
async def process_sum_command(message: Message, state: FSMContext):
    calendar = SimpleCalendar(show_alerts=True)
    calendar.set_dates_range(datetime(2022, 11, 1), datetime.now())
    await message.answer(
        text='Откуда вспоминать?',
        reply_markup=await calendar.start_calendar()
    )
    await state.set_state(AdminGetSumFSM.choose_from)
    await state.update_data(mode='chat')


@router.callback_query(SimpleCalendarCallback.filter(), StateFilter(AdminGetSumFSM.choose_from))
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
        await state.set_state(AdminGetSumFSM.choose_to)


@router.callback_query(SimpleCalendarCallback.filter(), StateFilter(AdminGetSumFSM.choose_to))
async def process_end_date(callback: CallbackQuery,
                           callback_data: SimpleCalendarCallback,
                           state: FSMContext,
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
            try:
                decorated_text = get_sum(from_date, date)
                if decorated_text:
                    await callback.message.edit_text(
                        text=f'📆 {from_date.strftime("%-d %B %Y")} - {date.strftime("%-d %B %Y")}\n\n'
                             f'{decorated_text}',
                        reply_markup=create_inline_kb(1, leave='Оставить в чате', delete='Удалить')
                    )
                    await bot.delete_message(chat_id=callback.message.chat.id,
                                             message_id=first_id)
                    await state.set_state(AdminGetSumFSM.leave_or_delete)

                else:
                    await callback.message.edit_text(
                        text=f'📆 {from_date.strftime("%-d %B %Y")} - {date.strftime("%-d %B %Y")}\n\n'
                             f'Там полный ноль по всем пунктам 🙆🏽‍♂️',
                        reply_markup=create_inline_kb(1, delete='Хорошо')
                                                    )
                    await bot.delete_message(chat_id=callback.message.chat.id,
                                             message_id=first_id)

                    await state.set_state(AdminGetSumFSM.leave_or_delete)

            except:
                await callback.message.edit_text(
                    text=f'📆 {from_date.strftime("%-d %B %Y")} - {date.strftime("%-d %B %Y")}\n\n'
                         f'Там полный ноль по всем пунктам 🙆🏽‍♂️',
                    reply_markup=create_inline_kb(1, delete='Хорошо')
                )
                await bot.delete_message(chat_id=callback.message.chat.id,
                                         message_id=first_id)

                await state.set_state(AdminGetSumFSM.leave_or_delete)

        if mode == 'xl':
            try:
                file = make_xlsx(from_date, date)
                if file:
                    await callback.message.answer_document(document=file,
                                                           caption=f'📆 {from_date.strftime("%-d %B %Y")}'
                                                                   f' - {date.strftime("%-d %B %Y")}\n')
                    await bot.delete_messages(chat_id=callback.message.chat.id,
                                              message_ids=[i for i in range(first_id,
                                                                            callback.message.message_id + 1)]
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

                    await state.set_state(AdminGetSumFSM.leave_or_delete)

            except:
                await callback.message.edit_text(
                    text=f'📆 {from_date.strftime("%-d %B %Y")} - {date.strftime("%-d %B %Y")}\n\n'
                         f'Там полный ноль по всем пунктам 🙆🏽‍♂️',
                    reply_markup=create_inline_kb(1, delete='Хорошо')
                )
                await bot.delete_message(chat_id=callback.message.chat.id,
                                         message_id=first_id)

                await state.set_state(AdminGetSumFSM.leave_or_delete)


@router.callback_query(F.data == 'leave', StateFilter(AdminGetSumFSM.leave_or_delete))
async def process_leave_choice(callback: CallbackQuery,
                               state: FSMContext):
    await callback.message.edit_text(text=callback.message.text)
    await callback.answer(text='Как скажете 🫡')
    await state.clear()


@router.callback_query(F.data == 'delete', StateFilter(AdminGetSumFSM.leave_or_delete))
async def process_leave_choice(callback: CallbackQuery,
                               state: FSMContext,
                               bot):
    await bot.delete_message(chat_id=callback.message.chat.id,
                             message_id=callback.message.message_id)
    await state.clear()


@router.message(Command('xl', prefix='.'))
async def process_sum_command(message: Message, state: FSMContext):
    calendar = SimpleCalendar(show_alerts=True)
    calendar.set_dates_range(datetime(2022, 11, 1), datetime.now())
    await message.answer(
        text='Откуда вспоминать?',
        reply_markup=await calendar.start_calendar()
    )
    await state.set_state(AdminGetSumFSM.choose_from)
    await state.update_data(mode='xl')


@router.message(Command('new_worksheet', prefix='.'))
async def process_new_worksheet(message: Message):
    if create_new_month_worksheet():
        await message.answer(text='Done')

    else:
        await message.answer(text='ERROR')