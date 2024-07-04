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
from tgbot.services.api_manager import OpenaiClient
from tgbot.config import Config
from tgbot.helpers.utils import get_openai_system_message, get_openai_system_message_ce_mfa
from tgbot.helpers.utils import create_absolute_path
from tgbot.modules.common.buttons import back_btn, close_dialog_back_btn
from .states import PracticState


async def on_start(data, dialog_manager: DialogManager):
    config: Config = dialog_manager.middleware_data.get("config")
    system_message = get_openai_system_message()
    openai_client = OpenaiClient(api_key=config.tg_bot.openai_api_key,
                                 system_message=system_message)

    # for key, value in dialog_manager.start_data.items():
    #     dialog_manager.dialog_data[key] = value

    dialog_manager.dialog_data["openai_client"] = openai_client


async def data_getter(dialog_manager: DialogManager,
                      i18n: I18nContext,
                      **_kwargs) -> Dict[str, Any | None]:

    _ = i18n.get
    tapchsolt_answer = dialog_manager.dialog_data.get("tapchsolt_answer", _('start_dialog'))

    return {
        "dialog_message": tapchsolt_answer,
        "back_btn": _("back_btn")
    }


async def get_ai_answer(message: types.Message,
                        message_input: MessageInput,
                        dialog_manager: DialogManager) -> None:
    chat_history: ChatMessageHistory = dialog_manager.dialog_data.get("chat_history", None)
    if not chat_history:
        chat_history = ChatMessageHistory()

    user_message = message.text
    translator = GoogleTranslator(source="auto", target="ru")
    translation = translator.translate(user_message)

    chat_history.add_user_message(
        HumanMessage(
                content=translation
        )
    )

    openai_client: OpenaiClient = dialog_manager.dialog_data["openai_client"]
    ai_answer = await openai_client.async_get_response(chat_history.messages)
    chat_history.add_ai_message(ai_answer)

    translator = GoogleTranslator(source="ru", target="ce")
    tapchsolt_answer = translator.translate(ai_answer.content)


    # TODO create voice chat
    # config: Config = dialog_manager.middleware_data.get("config")
    # system_message_mfa = get_openai_system_message_ce_mfa()
    # openai_client_mfa = OpenaiClient(api_key=config.tg_bot.openai_api_key,
    #                                  system_message=system_message_mfa)
    # chat_history_mfa = ChatMessageHistory()
    # chat_history_mfa.add_user_message(
    #     HumanMessage(
    #             content=tapchsolt_answer
    #     )
    # )
    # logging.info(chat_history_mfa.messages)
    # logging.info(system_message_mfa)
    # mfa_ce_text = await openai_client_mfa.async_get_response(chat_history_mfa.messages)


    # dialog_manager.dialog_data["tapchsolt_answer"] = f"{ai_answer.content}\n\n{tapchsolt_answer}\n\n{mfa_ce_text.content}"
    dialog_manager.dialog_data["tapchsolt_answer"] = tapchsolt_answer
    dialog_manager.dialog_data["chat_history"] = chat_history


practic_main_dialog = Dialog(
    Window(
        Format(text="{dialog_message}"),
        MessageInput(func=get_ai_answer,
                     content_types=types.ContentType.TEXT),
        close_dialog_back_btn,
        state=PracticState.START,
    ),
    on_start=on_start,
    getter=data_getter,
)