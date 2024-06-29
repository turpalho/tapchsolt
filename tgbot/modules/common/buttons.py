from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.kbd.button import OnClick
from aiogram_dialog.widgets.text import Const, Text, Format
from aiogram_dialog.widgets.widget_event import WidgetEventProcessor


async def go_back(call, button, dialog_manager: DialogManager):
    await dialog_manager.back()


back_btn = Button(
    text=Format("⬅️ {back_btn}"),
    id="back",
    on_click=go_back,
)


async def go_back_close_dialog(call: CallbackQuery, button, dialog_manager: DialogManager):
    await dialog_manager.done()
    if not dialog_manager.has_context():
        try:
            await call.message.delete()
        except:  # noqa
            pass


close_dialog_back_btn = Button(
    text=Format("⬅️ {back_btn}"),
    id="back",
    on_click=go_back_close_dialog,
)


async def go_next(call: CallbackQuery, button, dialog_manager: DialogManager):
    await dialog_manager.next()


next_btn = Button(
    text=Const("Далее ➡️"),
    id="next",
    on_click=go_next,
)
