from aiogram import Router

from .language_main import language_main_dialog

language_router = Router(name=__name__)
language_router.include_routers(
    language_main_dialog,
)