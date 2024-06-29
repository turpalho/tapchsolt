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
from infrastructure.database.models import Language, User
from tgbot.modules.users.dialogs.states import UserStates
from tgbot.helpers.utils import create_absolute_path
from tgbot.modules.common.buttons import back_btn, close_dialog_back_btn
from .states import UserRegistrationState


async def data_getter(dialog_manager: DialogManager,
                      i18n: I18nContext,
                      **_kwargs) -> Dict[str, Any | None]:
    _ = i18n.get

    user_nickname = dialog_manager.dialog_data.get("user_nickname", None)
    lang_name = dialog_manager.dialog_data.get("lang_name", None)
    languages = await Language.get_all()

    return {
        "select_lang": _("select_lang"),
        "languages": languages,
        "set_nickname": _("set_nickname"),
        "nickname": _("nickname"),
        "language": _("language"),
        "user_nickname": user_nickname,
        "lang_name": lang_name,
        "confirm_data": _("confirm_data"),
        "user_saved": _("user_saved"),
        "main_menu": _("main_menu"),
        "back_btn": _("back_btn"),
    }


async def select_native_language(call: types.CallbackQuery,
                                 select,
                                 dialog_manager: DialogManager,
                                 data: str):
    language = await Language.get(int(data))
    dialog_manager.dialog_data["lang_name"] = language.title
    dialog_manager.dialog_data["lang_code"] = language.code

    i18n: I18nContext = dialog_manager.middleware_data.get("i18n")
    await i18n.set_locale(language.code)
    await dialog_manager.next()


async def save_nickname(message: types.Message,
                        message_input: MessageInput,
                        dialog_manager: DialogManager,
                        ):
    dialog_manager.dialog_data["user_nickname"] = message.text
    await dialog_manager.next()


async def confirm_post_data(call: types.CallbackQuery,
                            button,
                            dialog_manager: DialogManager):
    lang_code = dialog_manager.dialog_data["lang_code"]
    user_nickname = dialog_manager.dialog_data["user_nickname"]
    await User.add_new(user_id=call.message.chat.id,
                       username=user_nickname,
                       language_code=lang_code,
                       tg_username=call.from_user.username,
                       tg_last_name=call.from_user.last_name,
                       tg_first_name=call.from_user.first_name,)
    await dialog_manager.next()


async def go_to_main_menu(call: types.CallbackQuery,
                          button,
                          dialog_manager: DialogManager):
    await dialog_manager.start(UserStates.start)


registration_main_dialog = Dialog(
    Window(
        Format(text="{select_lang}"),
        ScrollingGroup(
            Select(text=Format("{item.title}"),
                   id="user_main_data_users_language",
                   item_id_getter=lambda x: x.id,
                   items="languages",
                   on_click=select_native_language),
            id="data_languages_scr_group",
            width=2,
            height=4,
            hide_on_single_page=True,
        ),
        state=UserRegistrationState.START,
    ),
    Window(
        Format(text="{set_nickname}"),
        MessageInput(func=save_nickname,
                     content_types=types.ContentType.TEXT),
        back_btn,
        state=UserRegistrationState.SET_NICNAME,
    ),
    Window(
        Format(text="{confirm_data}!"
               "\n\t{nickname}: {user_nickname}"
               "\n\t{language}: {lang_name}"),
        Button(text=Format("🟢 {confirm_data}"),
               id="registration_main__confirm_data",
               on_click=confirm_post_data),
        back_btn,
        state=UserRegistrationState.CONFIRM_DATA,
    ),
    Window(
        Format(text="{user_saved}"),
         Button(text=Format("{main_menu}"),
               id="registration_main__go_main",
               on_click=go_to_main_menu),
        state=UserRegistrationState.SAVE_USER,
    ),
    getter=data_getter,
)