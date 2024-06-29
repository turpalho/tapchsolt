from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message

from tgbot.config import Config


class AddAdminFilter(BaseFilter):

    async def __call__(self, obj: Message, config: Config) -> bool:
        return obj.text == config.misc.add_admin_cmd
