from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from lexicone import LEXICON_RU
from filters.filters import IsUnknown
from aiogram import F
from functions.functions import write_user_to_env


router = Router()
router.message.filter(IsUnknown())


@router.message(Command('start'))
async def unknown_start_handler(message: Message):
    await message.answer(text=LEXICON_RU['first_meet'])


@router.message(F.text)
async def pass_try_handler(message: Message, password, user_ids):
    if message.text == password:
        user_ids.append(message.from_user.id)
        write_user_to_env(message.from_user.id)
        await message.reply(text=f'Теперь я тебе доверяю и полностью в твоем распоржении\n'
                                 f'list of instructions')
    else:
        await message.reply(text='Это хуйня какая-то')
