from aiogram import Router

from .practic_main import practic_main_dialog

practic_router = Router(name=__name__)
practic_router.include_routers(
    practic_main_dialog,
)