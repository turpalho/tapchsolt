import logging

from aiogram import F, Router, Bot
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram_dialog import DialogManager
from aiogram_i18n import I18nContext

from infrastructure.database.models import ConfigDb, User, Language
from tgbot.helpers.message_text import get_messages_text
from tgbot.config import Config
from tgbot.filters.user import AddAdminFilter
from tgbot.modules.users.dialogs.states import UserStates
from tgbot.modules.users.dialogs.registration.states import UserRegistrationState

logger = logging.getLogger(__name__)

user_handlers_router = Router()
user_handlers_router.message.filter(F.chat.type == "private")
user_handlers_router.callback_query.filter(F.message.chat.type == "private")


@user_handlers_router.message(AddAdminFilter())
async def add_admin(message: Message,
                    config: Config,
                    # repo: RequestsRepo,
                    state: FSMContext) -> None:
    await state.clear()

    if not message.from_user.id in config.tg_bot.admin_ids:
        config.tg_bot.admin_ids.append(message.from_user.id)
        await ConfigDb.update_admins_list(config.tg_bot.admin_ids)
        await message.answer(text=get_messages_text("ADD_ADMIN"))
    else:
        await message.answer(text=get_messages_text("EXISTED_ADMIN"))


@user_handlers_router.message(CommandStart())
async def process_start_command(message: Message,
                                i18n: I18nContext,
                                dialog_manager: DialogManager) -> None:
    user = await User.get(message.chat.id)
    if not user:
        await i18n.set_locale("en")
        await dialog_manager.start(UserRegistrationState.START)
        return
    await i18n.set_locale(user.language_code)
    await dialog_manager.start(UserStates.start)
