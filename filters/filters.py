from aiogram.filters import BaseFilter
from aiogram.types import Message


# UnKnown user
class IsUnknown(BaseFilter):
    async def __call__(self, message: Message, admin_ids, user_ids):
        return message.from_user.id not in (admin_ids + user_ids)


# Is in authorised user list
class IsUser(BaseFilter):
    async def __call__(self, message: Message, user_ids):
        return message.from_user.id in user_ids


def is_float(message: Message):
    try:
        float(message.text.strip())
        return True
    except ValueError:
        return False
