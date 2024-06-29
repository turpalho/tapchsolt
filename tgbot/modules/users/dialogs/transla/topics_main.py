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
from infrastructure.database.models import Topic, Element
from tgbot.helpers.utils import create_absolute_path
from tgbot.modules.common.buttons import back_btn, close_dialog_back_btn
from .states import SelectTopic, TopicsState
from .practic.states import PracticState


async def data_getter(dialog_manager: DialogManager,
                      i18n: I18nContext,
                      **_kwargs) -> Dict[str, Any | None]:
    _ = i18n.get

    topics = await Topic.get_all()

    return {
        "select_topic": _('select_topic'),
        "items": topics,
        "back_btn": _("back_btn")
    }


async def selected_topic(call: types.CallbackQuery,
                         select,
                         dialog_manager: DialogManager,
                         data: str):
    try:
        topic_id = int(data)
        logging.info(topic_id)
        first_element = await Element.get_by_attributes(topic_id=topic_id)
        last_element = await Element.get_last(topic_id=topic_id)
        element_data = {
            "topic_id": topic_id,
            "last_element_id": last_element.id,
            "element_id": first_element.id
        }
        await dialog_manager.start(
                    state=PracticState.START, data=element_data)
    except:
        pass


topics_main_dialog = Dialog(
    Window(
        Format(text="📚  {select_topic}"),
        ScrollingGroup(
            Select(text=Format("{item.title}"),
                   id="topics_data_topic_ids",
                   item_id_getter=lambda x: x.id,
                   items="items",
                   on_click=selected_topic),
            id="data_topics",
            width=1,
            height=8,
            hide_on_single_page=True,
        ),
        close_dialog_back_btn,
        state=TopicsState.START,
    ),
    getter=data_getter,
)