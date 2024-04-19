from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from lexicone import LEXICON_RU
from filters.filters import IsUnknown

router = Router()
router.message.filter(IsUnknown())


@router.message(Command('start'))
async def unknown_start_handler(message: Message):
    await message.answer(text=LEXICON_RU['first_meet'])

