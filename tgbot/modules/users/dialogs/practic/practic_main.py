from typing import Any, Dict

from aiogram import Bot, types
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.text import Format
from aiogram_i18n import I18nContext

from langchain_core.messages import AIMessage, HumanMessage
from langchain_community.chat_message_histories import ChatMessageHistory


# from services.broadcaster import broadcast_media_group, broadcast_plus
from tgbot.services.api_manager import GoogleClient
from tgbot.config import Config
from tgbot.helpers.utils import get_openai_system_message
from tgbot.modules.common.buttons import back_btn, close_dialog_back_btn
from .states import PracticState


async def on_start(data, dialog_manager: DialogManager):
    config: Config = dialog_manager.middleware_data.get("config")
    system_message = get_openai_system_message()

    google_client = GoogleClient(api_key=config.tg_bot.openai_api_key,
                                 system_message=system_message)

    dialog_manager.dialog_data["google_client"] = google_client


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
    chat_history.add_user_message(
        HumanMessage(
                content=user_message
        )
    )

    google_client: GoogleClient = dialog_manager.dialog_data["google_client"]
    ai_answer = await google_client.async_get_response(chat_history.messages)
    chat_history.add_ai_message(ai_answer)
    dialog_manager.dialog_data["tapchsolt_answer"] = ai_answer.content
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