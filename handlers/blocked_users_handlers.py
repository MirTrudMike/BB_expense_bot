from filters.filters import IsBlocked
from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.types import Message

router = Router()
router.message.filter(IsBlocked())


@router.message()
async def go_fuck_yourself(message: Message):
    await message.answer(text="Вы кто такие?!\n"
                              "Я вас не звал!\n"
                              "Идите на хуй отсюда!")