from aiogram import Router

from .user_main import users_main_dialog
from .registration import registration_router
from .profile import profile_router
from .practic import practic_router
from .translation import translation_router

user_dialogs_router = Router(name=__name__)
user_dialogs_router.include_routers(
    users_main_dialog,
    registration_router,
    profile_router,
    practic_router,
    translation_router,
)