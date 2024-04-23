from aiogram import Router, Bot
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery
from lexicone import LEXICON_RU
from filters.filters import IsAdmin, is_int
from aiogram import F
from functions.functions import decorate_expense
from functions.functions import find_expense_index_in_base, delete_record_by_base_index
from functions.functions import load_base, restore_base
from FSM.FSM_states import AdminFSM
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from keyboards.inline_kb import create_inline_kb

router = Router()
router.message.filter(IsAdmin())


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
async def delete_command_handler(message: Message,state: FSMContext):
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

    except: await message.answer(text='No element in BASE',
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















#not handled handler under