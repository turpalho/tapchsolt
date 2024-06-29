import asyncio
from datetime import datetime
import logging
import random
from typing import Any, Dict
from string import Template

from aiogram import Bot, types
from aiogram.exceptions import TelegramRetryAfter
from aiogram.utils.markdown import hlink, hbold, hcode, hitalic
from aiogram_dialog import Dialog, DialogManager, LaunchMode, Window
from aiogram_dialog.widgets.input import MessageInput, BaseInput
from aiogram_dialog.widgets.kbd import Button, ScrollingGroup, Select
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_i18n import I18nContext

# from services.broadcaster import broadcast_media_group, broadcast_plus
from infrastructure.database.models import Element, Language, Translate, Review, Media
from tgbot.helpers.utils import create_absolute_path
from tgbot.modules.common.buttons import back_btn, close_dialog_back_btn
from .states import PracticState


async def on_start(data, dialog_manager: DialogManager):
    for key, value in dialog_manager.start_data.items():
        dialog_manager.dialog_data[key] = value


async def data_getter(dialog_manager: DialogManager,
                      i18n: I18nContext,
                      **_kwargs) -> Dict[str, Any | None]:
    image_message = dialog_manager.dialog_data.get("img_message_id", None)
    if image_message:
        bot: Bot = dialog_manager.middleware_data.get("bot")
        await bot.delete_message(chat_id= dialog_manager.event.message.chat.id, message_id=int(image_message))
        dialog_manager.dialog_data["img_message_id"] = False

    element_id = dialog_manager.dialog_data["element_id"]
    topic_id = dialog_manager.dialog_data["topic_id"]

    # Send image
    # image = await Media.get_by_attributes(element_id=element_id, content_type=types.ContentType.PHOTO.value)
    # if image:
    #     is_image = dialog_manager.dialog_data.get("is_image", False)
    #     if not is_image:
    #         image_message = await dialog_manager.event.message.answer_photo(image.file_id)
    #         dialog_manager.dialog_data["img_message_id"] = image_message.message_id
    #         image_data = {
    #             "topic_id": topic_id,
    #             "last_element_id": dialog_manager.dialog_data["last_element_id"],
    #             "element_id": element_id,
    #             "is_image": True
    #         }
    #         await dialog_manager.start(PracticState.START, data=image_data)

    element = await Element.get_by_attributes(id=element_id,
                                              topic_id=topic_id)
    await element.awaitable_attrs.translates

    user_id = dialog_manager.event.message.chat.id
    review = await Review.get_by_attributes(element_id=element_id,
                                            user_id=user_id)
    if not review:
        review = await Review.add_new(count=0,
                                      user_id=user_id,
                                      element_id=element.id)

    dialog_manager.dialog_data["review"] = review

    correct_translate: Translate = None
    for translate in element.translates:
        if translate.language_code == i18n.locale:
            correct_translate = translate
            break

    random_translates = await Translate.get_random_translates(language_code=i18n.locale)
    correct_translate_id = correct_translate.id if correct_translate else None
    random_translate_ids = [t.id for t in random_translates]

    while correct_translate_id in random_translate_ids:
        random_translates = await Translate.get_random_translates(language_code=i18n.locale)
        random_translate_ids = [t.id for t in random_translates]

    translates = [
        correct_translate,
        *random_translates,
    ]
    random.shuffle(translates)

    # Set audio
    audio = await Media.get_by_attributes(element_id=element_id, content_type=types.ContentType.AUDIO.value)
    audio_file = MediaAttachment(types.ContentType.AUDIO, file_id=MediaId(audio.file_id))

    _ = i18n.get
    now = datetime.utcnow()
    try:
        days_since_last_review = (now - review.update_date).days
    except TypeError:
        days_since_last_review = (now - review.create_date).days

    # Каждый 10 дней снижаем уровень на 1
    decay = days_since_last_review // 10
    effective_count = max(review.count - decay, 0)
    element_text =f'{hbold(element.text.capitalize())}'

    if effective_count <= 0:
        element_text += f'\n\n{_("retention")}: 🌑'
    elif effective_count <= 4:
        element_text += f'\n\n{_("retention")}: 🌒'
    elif effective_count <= 8:
        element_text += f'\n\n{_("retention")}: 🌓'
    elif effective_count <= 12:
        element_text += f'\n\n{_("retention")}: 🌔'
    else:
        element_text += f'\n\n{_("retention")}: 🌕'

    return {
        "element": element_text,
        "correct_answer_id": correct_translate.id,
        "items": translates,
        # "translates": "\n".join([f"{nummer+1}.  {translate.text}" for nummer, translate in enumerate(translates)]),
        "audio": audio_file,
        "back_btn": _("back_btn")
    }


async def selected_topic(call: types.CallbackQuery,
                         select,
                         dialog_manager: DialogManager,
                         data: str):
    element_id: int = dialog_manager.dialog_data["element_id"]
    last_element_id: int = dialog_manager.dialog_data["last_element_id"]
    review: Review = dialog_manager.dialog_data["review"]

    _ = dialog_manager.middleware_data["i18n"].get

    if element_id != int(data):
        await call.answer(_("wrong_answer"))
    else:
        await Review.update(review.id, count=review.count+1)

        if element_id < last_element_id:
            element_id = element_id + 1
        else:
            topic_id = dialog_manager.dialog_data["topic_id"]
            element = await Element.get_by_attributes(topic_id=topic_id)
            element_id = element.id

    dialog_manager.dialog_data["element_id"] = element_id
    dialog_manager.dialog_data["last_element_id"] = last_element_id
    dialog_manager.dialog_data["img_message_id"] = dialog_manager.dialog_data.get("img_message_id", None)


async def on_process_result(data, result, dialog_manager: DialogManager):
    if isinstance(result, dict):
        for key, value in result.items():
            dialog_manager.dialog_data[key] = value

practic_topic_main_dialog = Dialog(
    Window(
        DynamicMedia("audio"),
        Format("{element}"),
        ScrollingGroup(
            Select(text=Format("➖ {item.text} ➖"),
                   id="elements_data_translates_ids",
                   item_id_getter=lambda x: x.element_id,
                   items="items",
                   on_click=selected_topic),
            id="data_topics",
            width=1,
            height=4,
            hide_on_single_page=True,
        ),
        close_dialog_back_btn,
        state=PracticState.START,
    ),
    getter=data_getter,
    on_start=on_start,
    on_process_result=on_process_result,
)