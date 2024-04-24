from aiogram import Router, Bot
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery
from lexicone import LEXICON_RU
from filters.filters import IsUnknown
from aiogram import F
from functions.functions import write_user_to_env, write_user_to_block
from FSM.FSM_states import PassTryFSM
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
import asyncio
from keyboards.inline_kb import create_inline_kb
from keyboards.regular_kb import reg_categories_kb
from functions.chelduler_functions import set_schedulers
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from functions.set_menu import set_main_menu

router = Router()
router.message.filter(IsUnknown())


@router.message(Command('start'), StateFilter(default_state))
async def unknown_start_handler(message: Message, state: FSMContext):
    await message.answer(text=LEXICON_RU['first_meet'])
    await state.set_state(PassTryFSM.input_pass)
    await state.update_data(tries=4,
                            first_id=message.message_id,
                            user_id=message.from_user.id)


@router.message(F.text, StateFilter(PassTryFSM.input_pass))
async def pass_try_handler(message: Message, state: FSMContext, password, blocked_ids):
    if message.text == password:
        await message.answer(text=LEXICON_RU['joke'])
        await asyncio.sleep(8)
        await message.answer(text='🤡 Шутка 🤡\n'
                                  'Следить за таким я пока не умею 🤫',
                             reply_markup=create_inline_kb(1, lol="Ха-Ха 😂"))
        await state.set_state(PassTryFSM.get_informed)

    else:
        data = await state.get_data()
        tries = data['tries']
        user_id = data['user_id']
        if tries > 0:
            await message.answer(text=f'Ну нет..\n\n'
                                     f'Осталось {tries} попыток')
            await state.update_data(tries=tries - 1)

        else:
            await message.answer(text="Ну всё...\nТеперь я с тобой не дружу")
            blocked_ids.append(user_id)
            write_user_to_block(user_id)
            await state.clear()


@router.callback_query(F.data == 'lol', StateFilter(PassTryFSM.get_informed))
async def give_instructions(callback: CallbackQuery,
                            state: FSMContext,
                            user_ids: list,
                            bot: Bot,
                            apscheduler: AsyncIOScheduler):
    chat_id = callback.message.chat.id
    data = await state.get_data()
    first_id = data['first_id']
    user_id = data['user_id']
    user_ids.append(user_id)
    write_user_to_env(user_id)
    await asyncio.sleep(3)

    await bot.delete_messages(chat_id=chat_id,
                              message_ids=[first_id,
                                           first_id + 1,
                                           first_id + 2,
                                           first_id + 4])

    await bot.edit_message_text(chat_id=chat_id,
                                message_id=first_id + 3,
                                text="Вот теперь давай расскажу, что я на самом деле умею!\n\n"
                                     "Через 5 секунд внизу появится быстрые кнопки ↘️")
    await asyncio.sleep(5)

    for i in range(4,0,-1):
        await bot.edit_message_text(chat_id=chat_id,
                                    message_id=first_id + 3,
                                    text=f"Вот теперь давай расскажу, что я на самом деле умею!\n\n"
                                         f"Через {i} секунд внизу появится быстрые кнопки ↘️")
        await asyncio.sleep(2)

    await bot.delete_message(chat_id=chat_id,
                             message_id=first_id + 3)

    await bot.send_message(chat_id=chat_id,
                           text=f"Вот они ↘️",
                           reply_markup=reg_categories_kb.as_markup())

    await asyncio.sleep(4)

    await bot.send_message(chat_id=chat_id,
                           text=f"↙️ А здесь меню со всеми командами которые я пока знаю.")

    await asyncio.sleep(4)

    await bot.send_message(chat_id=chat_id,
                           text=f"🧛🏼‍♂️ И еще я буду иногда напоминать о себе, и приставать с вопросами")

    await state.clear()

    set_schedulers(bot=bot, user_ids=[user_id,], scheduler=apscheduler)


