import json
import logging
import re

from aiogram import F, Router, Bot
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.types import Message, ContentType, FSInputFile, URLInputFile
from aiogram.fsm.context import FSMContext
from aiogram_dialog import DialogManager

from tgbot.config import Config
from tgbot.filters.admin import AdminFilter
from infrastructure.database.models import (Language)
# from tgbot.keyboards.admin import get_keyboard

logger = logging.getLogger(__name__)

admin_handlers_router = Router()
admin_handlers_router.message.filter(AdminFilter())
admin_handlers_router.message.filter(F.chat.type == "private")
admin_handlers_router.callback_query.filter(F.message.chat.type == "private")


@admin_handlers_router.message(Command(commands=["add_languages"]))
async def add_main_languages(message: Message, config: Config) -> None:
    languages = {
        'ce': '🏴  Нохчийн',
        'en': '🇺🇲  English',
        'ar': '🇸🇦  اَلْعَرَبِيَّةُ',
        'tur': '🇹🇷  Türkçe',
        'ru': '🇷🇺 Русский',
        'uk': '🇺🇦  Українська',
        'de': '🇩🇪  Deutsch',
        'fr': '🇫🇷  Deutsch',
    }

    for code, title in languages.items():
        await Language.add_new(code=code, title=title)
    text = "Языки добавлены в базу данных!"
    await message.answer(text)


@admin_handlers_router.message(Command(commands=["help"]))
async def get_help(message: Message,
                       config: Config,
                       dialog_manager: DialogManager) -> None:
    await message.answer("""
/add_languages - add languages

/del_admin
""")


@admin_handlers_router.message(Command(commands=["del_admin"]))
async def delete_admin(message: Message,
                    #    dataFacade: DataFacade,
                       config: Config) -> None:
    config.tg_bot.admin_ids.remove(message.from_user.id)
    # await dataFacade.update_admin_ids(config.tg_bot.admin_ids)

    text = "Администратор удален"
    await message.answer(text)