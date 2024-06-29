from aiogram import Router

from .user_main import users_main_dialog
from .registration import registration_router
# from .transla import topics_router
from .profile import profile_router
from .practic import practic_router

user_dialogs_router = Router(name=__name__)
user_dialogs_router.include_routers(
    users_main_dialog,
    registration_router,
    # topics_router,
    profile_router,
    practic_router
)