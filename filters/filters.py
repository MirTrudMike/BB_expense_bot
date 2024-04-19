from aiogram.filters import BaseFilter
from aiogram.types import Message


# UnKnown user
class IsUnknown(BaseFilter):
    async def __call__(self, message: Message, admin_ids, user_ids):
        return message.from_user.id not in (admin_ids + user_ids)


