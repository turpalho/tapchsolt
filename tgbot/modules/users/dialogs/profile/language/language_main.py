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
from infrastructure.database.models import User, Language
from tgbot.helpers.utils import create_absolute_path
from tgbot.modules.common.buttons import back_btn, close_dialog_back_btn
from .states import LanguageState


async def data_getter(dialog_manager: DialogManager,
                      i18n: I18nContext,
                      **_kwargs) -> Dict[str, Any | None]:
    _ = i18n.get

    languages = await Language.get_all()

    return {
        "select_lang": _("select_lang"),
        "items": languages,
        "back_btn": _("back_btn"),
    }

async def select_language(call: types.CallbackQuery,
                          button: Button,
                          dialog_manager: DialogManager,
                          data: str):
    await User.update(dialog_manager.event.message.chat.id, language_code=data)

    i18n: I18nContext = dialog_manager.middleware_data["i18n"]
    await i18n.set_locale(data)
    await call.answer(i18n.get("language_edited"))
    await dialog_manager.done()

language_main_dialog = Dialog(
    Window(
        Format(text="🔄  {select_lang}"),
        ScrollingGroup(
            Select(text=Format("{item.title}"),
                   id="user_main_data_users_language",
                   item_id_getter=lambda x: x.code,
                   items="items",
                   on_click=select_language),
            id="data_languages_scr_group",
            width=1,
            height=8,
            hide_on_single_page=True,
        ),
        close_dialog_back_btn,
        state=LanguageState.START,
    ),
    getter=data_getter
)