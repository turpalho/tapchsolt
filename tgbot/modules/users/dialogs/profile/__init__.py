from aiogram import Router

from .profile_main import profile_main_dialog
from .language import language_router

profile_router = Router(name=__name__)
profile_router.include_routers(
    profile_main_dialog,
    language_router
)