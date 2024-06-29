import asyncio
import logging
from typing import Any, Dict
from string import Template

from aiogram import Bot, types
from aiogram.exceptions import TelegramRetryAfter
from aiogram.utils.markdown import hlink, hbold, hcode, hitalic
from aiogram_dialog import Dialog, DialogManager, LaunchMode, Window
from aiogram_dialog.widgets.input import MessageInput, BaseInput
from aiogram_dialog.widgets.kbd import Button, ScrollingGroup, Select
from aiogram_dialog.widgets.text import Const, Format
from aiogram_i18n import I18nContext

# from services.broadcaster import broadcast_media_group, broadcast_plus
from infrastructure.database.models import User
from tgbot.helpers.utils import create_absolute_path
from tgbot.modules.common.buttons import back_btn, close_dialog_back_btn
from .states import ProfileState
from .language.states import LanguageState


async def data_getter(dialog_manager: DialogManager,
                      i18n: I18nContext,
                      **_kwargs) -> Dict[str, Any | None]:
    _ = i18n.get

    user = await User.get(dialog_manager.event.message.chat.id)

    return {
        "language": f"🔄  {_('language').lower()}",
        "user": f"🔅  {_("nickname")}: {user.username}",
        "back_btn": _("back_btn")
    }

async def edit_language(call: types.CallbackQuery,
                        button: Button,
                        dialog_manager: DialogManager):
    await dialog_manager.start(state=LanguageState.START)


profile_main_dialog = Dialog(
    Window(
        Format("{user}"),
        Button(text=Format("{language}"),
            id="view_language",
            on_click=edit_language),
        close_dialog_back_btn,
        state=ProfileState.START,
    ),
    getter=data_getter
)