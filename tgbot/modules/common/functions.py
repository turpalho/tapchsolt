import logging

from aiogram import Bot, exceptions
from aiogram_dialog import DialogManager, ShowMode


async def rerender_window(dialog_manager: DialogManager, chat_id: int):
    bot = dialog_manager.middleware_data['bot']
    assert isinstance(bot, Bot)

    msg_id = dialog_manager.current_stack().last_message_id
    await dialog_manager.show(show_mode=ShowMode.EDIT)
    try:
        assert msg_id
        await bot.delete_message(message_id=msg_id,
                                 chat_id=chat_id)
    except (AssertionError, exceptions.AiogramError):
        logging.warning("Stack update error")
