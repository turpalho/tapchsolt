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

# Убираем GoogleTranslator - общаемся с Gemini напрямую

# from services.broadcaster import broadcast_media_group, broadcast_plus
from infrastructure.database.models import Language
from tgbot.services.api_manager import GoogleClient
from tgbot.config import Config
from tgbot.helpers.utils import get_ai_system_message
# Удаляем неиспользуемый импорт create_absolute_path
from tgbot.modules.common.buttons import back_btn, close_dialog_back_btn
from .states import TranslationState


async def on_start(data, dialog_manager: DialogManager):
    config: Config = dialog_manager.middleware_data.get("config")
    system_message = get_ai_system_message()

    google_client = GoogleClient(api_key=config.tg_bot.gemini_api_key,
                                 system_message=system_message,
                                 proxy_url=config.tg_bot.proxy_url)

    # Тестируем прокси при первом запуске
    if config.tg_bot.proxy_url:
        await google_client.test_proxy_connection()

    dialog_manager.dialog_data["google_client"] = google_client


async def data_getter(dialog_manager: DialogManager,
                      i18n: I18nContext,
                      **_kwargs) -> Dict[str, Any | None]:

    _ = i18n.get
    ai_answer = dialog_manager.dialog_data.get(
        "ai_answer", _('start_translate'))
    src_lang_name = dialog_manager.dialog_data.get("src_lang_name", None)
    target_lang_name = dialog_manager.dialog_data.get("target_lang_name", None)
    languages = await Language.get_all()

    return {
        "select_src_lang": _("select_src_lang"),
        "select_target_lang": _("select_target_lang"),
        "dialog_message": ai_answer,
        "languages": languages,
        "src_lang_name": src_lang_name,
        "target_lang_name": target_lang_name,
        "back_btn": _("back_btn")
    }


async def get_ai_answer(message: types.Message,
                        message_input: MessageInput,
                        dialog_manager: DialogManager) -> None:
    bot: Bot = dialog_manager.middleware_data.get("bot")

    # Отправляем статус "typing"
    await bot.send_chat_action(
        chat_id=message.chat.id,
        action="typing"
    )

    # Отправляем начальное сообщение для последующего редактирования
    thinking_message = await bot.send_message(
        chat_id=message.chat.id,
        text="🧠 Ойла йеш ву..."
    )

    try:
        # Получаем историю сообщений или создаем новую
        chat_history: ChatMessageHistory = dialog_manager.dialog_data.get(
            "chat_history", None)
        if not chat_history:
            chat_history = ChatMessageHistory()

        user_message = message.text

        # Добавляем сообщение пользователя в историю
        chat_history.add_user_message(
            HumanMessage(content=user_message)
        )

        # Ограничиваем историю до 10 сообщений (20 объектов: 10 пользователя + 10 ИИ)
        if len(chat_history.messages) > 20:
            # Удаляем старые сообщения, оставляем последние 20
            chat_history.messages = chat_history.messages[-20:]

        # Получаем ответ от Gemini с thinking progress
        google_client: GoogleClient = dialog_manager.dialog_data["google_client"]

        # Используем thinking progress с редактированием одного сообщения
        final_answer = None
        async for thinking_update in google_client.async_get_response_with_thinking(chat_history.messages):
            # Редактируем сообщение с текущим статусом мышления
            try:
                await bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=thinking_message.message_id,
                    text=thinking_update
                )
            except Exception as edit_error:
                # Если редактирование не удалось (например, текст не изменился), игнорируем
                pass

            # Если это не статус мышления (не начинается с 🧠), значит это финальный ответ
            if not thinking_update.startswith("🧠"):
                final_answer = thinking_update
                break

        # Удаляем сообщение с thinking после получения ответа
        try:
            await bot.delete_message(
                chat_id=message.chat.id,
                message_id=thinking_message.message_id
            )
        except Exception:
            # Если удалить не удалось, не критично
            pass

        if final_answer and not final_answer.startswith("❌"):
            # Создаем объект AIMessage для истории
            from langchain_core.messages import AIMessage
            ai_message = AIMessage(content=final_answer)
            chat_history.add_ai_message(ai_message)
            dialog_manager.dialog_data["chat_history"] = chat_history

        # Обновляем данные диалога с финальным ответом
        dialog_manager.dialog_data["ai_answer"] = final_answer or "❌ Не удалось получить ответ"

    except Exception as e:
        # Пытаемся удалить thinking сообщение в случае ошибки
        try:
            await bot.delete_message(
                chat_id=message.chat.id,
                message_id=thinking_message.message_id
            )
        except Exception:
            pass

        # Детальная обработка ошибок
        import traceback
        error_details = traceback.format_exc()
        print(f"Ошибка в get_ai_answer: {error_details}")  # Для консоли

        error_message = f"❌ Ошибка: {str(e)}"
        dialog_manager.dialog_data["ai_answer"] = error_message


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
