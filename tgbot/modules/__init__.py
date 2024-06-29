# flake8: noqa
from aiogram import Router

# from .admins.dialogs import admin_dialogs_router
from .admins.admin_handlers import admin_handlers_router
from .users.user_handlers import user_handlers_router
from .users.dialogs import user_dialogs_router

common_router = Router()
common_router.include_routers(
    admin_handlers_router,
    user_handlers_router,
    user_dialogs_router,
    # admin_dialogs_router,
)
