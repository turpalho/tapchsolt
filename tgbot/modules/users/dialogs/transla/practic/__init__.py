from aiogram import Router

# from .practic_main import practic_topic_main_dialog


practic_topic_router = Router(name=__name__)
practic_topic_router.include_routers(
    # practic_topic_main_dialog,
)