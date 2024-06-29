from aiogram import Router

from .registration_main import registration_main_dialog

registration_router = Router(name=__name__)
registration_router.include_routers(
    registration_main_dialog,
)