from aiogram.filters import BaseFilter
from aiogram.types import Message


# UnKnown user
class IsUnknown(BaseFilter):
    async def __call__(self, message: Message, admin_id, user_ids):
        return message.from_user.id not in user_ids and message.from_user.id != admin_id


class IsAdmin(BaseFilter):
    async def __call__(self, message: Message, admin_id, user_ids):
        return message.from_user.id == admin_id


# Is in authorised user list
class IsUser(BaseFilter):
    async def __call__(self, message: Message, user_ids):
        return message.from_user.id in user_ids


class IsBlocked(BaseFilter):
    async def __call__(self, message: Message, blocked_ids):
        return message.from_user.id in blocked_ids


def is_float(message: Message):
    try:
        float(message.text.strip())
        return True
    except ValueError:
        return False


def is_int(message: Message):
    try:
        int(message.text.strip())
        return True
    except ValueError:
        return False

