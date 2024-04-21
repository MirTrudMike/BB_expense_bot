from aiogram.utils.keyboard import ReplyKeyboardBuilder
from config_data.info import categories
from aiogram.types import KeyboardButton
from lexicone import LEXICON_RU

kb_builder = ReplyKeyboardBuilder()

categories_buttons = [KeyboardButton(text=LEXICON_RU[f'{ct}']) for ct in categories]
reg_categories_kb = kb_builder.row(*categories_buttons, width=3)
