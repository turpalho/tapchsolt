from typing import Any, Dict
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.text import Format
from aiogram_i18n import I18nContext

from .states import UserStates
from .practic.states import PracticState
from .profile.states import ProfileState
from .translation.states import TranslationState


async def data_getter(dialog_manager: DialogManager,
                      i18n: I18nContext,
                      **_kwargs) -> Dict[str, Any | None]:
    _ = i18n.get

    return {
        "main_menu": _("main_menu"),
        "tapchsolt": _("tapchsolt"),
        "translate": _("translate"),
        "instruction": _("instruction"),
        "profile": _("profile"),
    }


async def go_to_dialog(call: CallbackQuery,
                    button: Button,
                    dialog_manager: DialogManager):
    await dialog_manager.start(state=PracticState.START)


async def go_translate(call: CallbackQuery,
                       button: Button,
                       dialog_manager: DialogManager):
    await dialog_manager.start(state=TranslationState.START)


async def get_user_id(call: CallbackQuery,
                      button: Button,
                      dialog_manager: DialogManager):
    await call.answer()
    return

async def go_to_profile(call: CallbackQuery,
                      button: Button,
                      dialog_manager: DialogManager):
    await dialog_manager.start(state=ProfileState.START)


users_main_dialog = Dialog(
    Window(
        Format("〽  {main_menu}"),
        Button(text=Format("👥  {tapchsolt}"),
            id="view_dialog",
            on_click=go_to_dialog),
        Button(text=Format("📚  {translate}"),
            id="view_translate",
            on_click=go_translate),
        Button(text=Format("ℹ  {instruction}"),
            id="view_instruct",
            on_click=get_user_id),
        Button(text=Format("🔰  {profile}"),
            id="view_profile",
            on_click=go_to_profile),
        state=UserStates.start,
    ),
    getter=data_getter
)

