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
from .dialogs.elements.states import ElementState
from infrastructure.database.models import (Language,
                                            Element,
                                            Topic,
                                            Translate,
                                            Media)
# from tgbot.keyboards.admin import get_keyboard

logger = logging.getLogger(__name__)

admin_handlers_router = Router()
admin_handlers_router.message.filter(AdminFilter())
admin_handlers_router.message.filter(F.chat.type == "private")
admin_handlers_router.callback_query.filter(F.message.chat.type == "private")


@admin_handlers_router.message(Command(commands=["add_languages"]))
async def add_main_languages(message: Message, config: Config) -> None:
    languages = {
        'en': '🇺🇲  English',
        'ru': '🇷🇺 Русский',
        'uk': '🇺🇦  Українська',
        'ar': '🇸🇦  اَلْعَرَبِيَّةُ',
        'edo': '🇳🇬  Ẹ̀dó',
        'tur': '🇹🇷  Türkçe'
    }

    for code, title in languages.items():
        await Language.add_new(code=code, title=title)
    text = "Языки добавлены в базу данных!"
    await message.answer(text)


@admin_handlers_router.message(Command(commands=["add_main_topics"]))
async def add_main_topics(message: Message, config: Config) -> None:
    topics = {
        '1  👋  Willkommen': 'A1',
        '2  🇩🇪  Alte Heimat, neue Heimat': 'A1',
        '3  🏢  Häuser und Wohnungen': 'A1',
        '4  🚼  Familienleben': 'A1',
        '5  🌗  Der Tag und die Woche': 'A1',
        '6  🍔  Guten Appetit': 'A1',
        '7  🔧  Arbeit und Beruf': 'A1',
        '8  📆  Gute Besserung!': 'A1',
        '9  🚋  Wege durch die Stadt': 'A1',
        '10 🔄  Mein Leben': 'A1',
        '11 💼  Ämter und Behörden': 'A1',
        '12 🛒  Im Kaufhaus': 'A1',
        '13 ✈  Auf Reisen': 'A1',
        '14 🏠  Zusammen leben': 'A1',
    }

    for title, level_code in topics.items():
        await Topic.add_new(title=title, level_code=level_code)
    text = "Темы добавлены в базу данных!"
    await message.answer(text)


@admin_handlers_router.message(Command(commands=["add_main_elements"]))
async def add_main_elements(message: Message, config: Config) -> None:
    languages_codes = {
        "russian": "ru",
        "english": "en",
        "ukrain": "uk",
        "edo(nigeria)": "edo",
        "arabic": "ar",
        "turkish": "tur"
    }

    elements_data = None

    with open('source/words.json') as f:
        elements_data: dict = json.load(f)

    for topic_id, words  in elements_data.items():
        for word, translates in words.items():
            if len(word.split()) == 1:
                word = word.capitalize()
            element = await Element.add_new(text=word,
                                            topic_id=int(topic_id))

            # Adding auidio
            # with open(f"source/audios/{word}.mp3", mode="r") as audio_file:
            file = FSInputFile(f"source/audios/{word}.mp3", filename="Adam")
            audio_message = await message.answer_audio(audio=file, caption=word)
            file_id = audio_message.audio.file_id
            logging.info(f"File id: {file_id}, Word: {word}")
            await Media.add_new(file_id=file_id,
                                content_type=ContentType.AUDIO,
                                element_id=element.id)

            # Adding image
            with open('source/images.json') as f:
                images_data: dict = json.load(f)

            for data in images_data:
                for word_name, image_url in data.items():
                    if word == word_name:
                        image_file = URLInputFile(image_url)
                        image_message = await message.answer_photo(photo=image_file)
                        await Media.add_new(file_id=image_message.photo[0].file_id,
                                            content_type=ContentType.PHOTO,
                                            element_id=element.id)

            for code, translate in translates.items():
                if len(translate.split()) == 1:
                    translate = translate.capitalize()
                await Translate.add_new(
                    text=translate,
                    language_code=languages_codes[code],
                    element_id=element.id
                )

    text = "Элементы добавлены в базу данных!"
    await message.answer(text)


@admin_handlers_router.message(Command(commands=["add_element"]))
async def add_elements(message: Message,
                       config: Config,
                       dialog_manager: DialogManager) -> None:
    await dialog_manager.start(ElementState.START)


@admin_handlers_router.message(Command(commands=["help"]))
async def get_help(message: Message,
                       config: Config,
                       dialog_manager: DialogManager) -> None:
    await message.answer("""
/add_languages - add languages

/add_main_topics - add topics

/add_main_elements


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