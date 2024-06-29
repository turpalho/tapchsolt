from aiogram import Router

from .topics_main import topics_main_dialog
from .practic import practic_topic_router

topics_router = Router(name=__name__)
topics_router.include_routers(
    topics_main_dialog,
    practic_topic_router,
)