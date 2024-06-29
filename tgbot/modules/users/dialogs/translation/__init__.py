from aiogram import Router

from .translation_main import translation_main_dialog

translation_router = Router(name=__name__)
translation_router.include_routers(
    translation_main_dialog,
)