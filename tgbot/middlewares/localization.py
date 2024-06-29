from typing import Callable, Dict, Any, Awaitable, Tuple

from aiogram_i18n import I18nMiddleware
from aiogram import BaseMiddleware
from aiogram import types


LANG_STORAGE = {}


class LocalizationMiddleware(I18nMiddleware):
    async def get_locale(self, event: types.TelegramObject, data: Dict[str, Any]) -> str:
        """
        Detect current user locale based on event and context.

        **This method must be defined in child classes**

        :param event:
        :param data:
        :return:
        """

        if isinstance(event, types.Message):
            user_id = event.from_user.id
        elif isinstance(event, types.CallbackQuery):
            user_id = event.message.from_user.id

        if LANG_STORAGE.get(user_id) is None:
            LANG_STORAGE[user_id] = "en"

        language = data['locale'] = LANG_STORAGE[user_id]
        return language


class LocalMiddleware(BaseMiddleware):
    def __init__(self, _) -> None:
        self._ = _

    async def __call__(
            self,
            handler: Callable[[types.Message, Dict[str, Any]], Awaitable[Any]],
            event: types.Message,
            data: Dict[str, Any]
    ) -> Any:
        data['_'] = self._
        return await handler(event, data)