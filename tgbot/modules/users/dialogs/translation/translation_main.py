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

from langchain_core.messages import AIMessage, HumanMessage
from langchain_community.chat_message_histories import ChatMessageHistory

from deep_translator import GoogleTranslator

# from services.broadcaster import broadcast_media_group, broadcast_plus
from infrastructure.database.models import Language
from tgbot.services.api_manager import OpenaiClient
from tgbot.config import Config
from tgbot.helpers.utils import get_openai_system_message
from tgbot.helpers.utils import create_absolute_path
from tgbot.modules.common.buttons import back_btn, close_dialog_back_btn
from .states import TranslationState


async def on_start(data, dialog_manager: DialogManager):
    pass


async def data_getter(dialog_manager: DialogManager,
                      i18n: I18nContext,
                      **_kwargs) -> Dict[str, Any | None]:

    _ = i18n.get
    translated = dialog_manager.dialog_data.get("translated", _('start_translate'))
    src_lang_name = dialog_manager.dialog_data.get("src_lang_name", None)
    target_lang_name = dialog_manager.dialog_data.get("target_lang_name", None)
    languages = await Language.get_all()

    return {
        "select_src_lang": _("select_src_lang"),
        "select_target_lang": _("select_target_lang"),
        "dialog_message": translated,
        "languages": languages,
        "src_lang_name": src_lang_name,
        "target_lang_name": target_lang_name,
        "back_btn": _("back_btn")
    }


async def get_ai_answer(message: types.Message,
                        message_input: MessageInput,
                        dialog_manager: DialogManager) -> None:
    src_lang_code = dialog_manager.dialog_data["src_lang_code"]
    target_lang_code = dialog_manager.dialog_data["target_lang_code"]
    translator = GoogleTranslator(source=src_lang_code, target=target_lang_code)

    user_message = message.text
    translated = translator.translate(user_message)
    dialog_manager.dialog_data["translated"] = translated


async def select_src_language(call: types.CallbackQuery,
                              select,
                              dialog_manager: DialogManager,
                              data: str):
    language = await Language.get(int(data))
    dialog_manager.dialog_data["src_lang_name"] = language.title
    dialog_manager.dialog_data["src_lang_code"] = language.code
    await dialog_manager.next()


async def select_target_language(call: types.CallbackQuery,
                                 select,
                                 dialog_manager: DialogManager,
                                 data: str):
    language = await Language.get(int(data))
    dialog_manager.dialog_data["target_lang_name"] = language.title
    dialog_manager.dialog_data["target_lang_code"] = language.code
    await dialog_manager.next()


translation_main_dialog = Dialog(
    Window(
        Format(text="⤴  {select_src_lang}  ⤴"),
        ScrollingGroup(
            Select(text=Format("{item.title}"),
                   id="user_main_data_users_language",
                   item_id_getter=lambda x: x.id,
                   items="languages",
                   on_click=select_src_language),
            id="data_languages_scr_group",
            width=2,
            height=4,
            hide_on_single_page=True,
        ),
        close_dialog_back_btn,
        state=TranslationState.START,
    ),
    Window(
        Format(text="⤵  {select_target_lang}  ⤵"),
        ScrollingGroup(
            Select(text=Format("{item.title}"),
                   id="user_main_data_users_language",
                   item_id_getter=lambda x: x.id,
                   items="languages",
                   on_click=select_target_language),
            id="data_languages_scr_group",
            width=2,
            height=4,
            hide_on_single_page=True,
        ),
        back_btn,
        state=TranslationState.SELECT_TARGET_LANGUAGE,
    ),
    Window(
        Format(text="{dialog_message}"),
        MessageInput(func=get_ai_answer,
                     content_types=types.ContentType.TEXT),
        close_dialog_back_btn,
        state=TranslationState.TRANSLATE,
    ),
    on_start=on_start,
    getter=data_getter,
)