"""Main module for the bot."""
import asyncio
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import DefaultKeyBuilder, RedisStorage
from aiogram_dialog import setup_dialogs
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram_i18n.cores.fluent_runtime_core import FluentRuntimeCore
from aiogram_i18n import I18nMiddleware

from infrastructure.database.models import ConfigDb
from infrastructure.database.setup import create_db, dispose_db

from tgbot.middlewares.album_middleware import AlbumMiddleware
# from tgbot.middlewares.scheduler_middleware import SchedulerMiddleware
from tgbot.middlewares.localization import LocalizationMiddleware, LocalMiddleware
from tgbot.config import Config, load_config
from tgbot.middlewares.config import ConfigMiddleware
# from tgbot.misc.logging import LoggingPackagePathFilter
from tgbot.services import broadcaster
from tgbot.modules import common_router

logger = logging.getLogger(__name__)

bot_commands = [
    types.BotCommand(command="/start", description="Main menu"),
    types.BotCommand(command="/help", description="Help"),
    types.BotCommand(command="/id", description="Get your Telegram ID"),
]


async def on_startup(bot: Bot, admin_ids: list[int]):
    """
    Send a message to the admin users when the bot is started.

    Args:
        bot (Bot): The bot instance.
        admin_ids (list[int]): The list of admin user ids.
    """
    await broadcaster.broadcast(bot, admin_ids, "Бот запущен")


def register_global_middlewares(dp: Dispatcher,
                                config: Config,
                                # scheduler: AsyncIOScheduler,
                                # session_pool
                                ):
    middleware_types = [
        ConfigMiddleware(config),
        # SchedulerMiddleware(scheduler),
    ]

    for middleware_type in middleware_types:
        dp.message.outer_middleware(middleware_type)
        dp.callback_query.outer_middleware(middleware_type)
        dp.inline_query.outer_middleware(middleware_type)
        dp.my_chat_member.outer_middleware(middleware_type)
        # dp.chat_member.outer_middleware(middleware_type)

    dp.message.middleware(AlbumMiddleware())


def get_storage(config: Config):
    """
    Return storage based on the provided configuration.

    Args:
        config (Config): The configuration object.

    Returns:
        Storage: The storage object based on the configuration.

    """
    if config.tg_bot.use_redis:
        return RedisStorage.from_url(
            config.redis.dsn(),
            key_builder=DefaultKeyBuilder(with_bot_id=True,
                                          with_destiny=True),
        )
    return MemoryStorage()


async def restore_config(config: Config):
    db_config = await ConfigDb.get(1)
    if db_config:
        config.synchronize_attrs(db_config)
    else:
        await ConfigDb.create(str(config.tg_bot.admin_ids))


async def main():
    """Start the project."""
    logging.basicConfig(
        level=logging.INFO,
        format=u'%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s',
    )
    logger.info("Starting bot")

    config = load_config(".env")
    storage = get_storage(config)

    bot = Bot(token=config.tg_bot.token,
              default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher(storage=storage)
    await bot.set_my_commands(commands=bot_commands)

    # We register regular routers
    dp.include_routers(common_router)
    setup_dialogs(dp)

    db_engine = await create_db(config.db)

    # scheduler = AsyncIOScheduler()
    # scheduler.start()
    i18n = LocalizationMiddleware(
        core=FluentRuntimeCore(
            path="locales/{locale}/LC_MESSAGES"
        )
    )
    i18n.setup(dispatcher=dp)

    await restore_config(config)
    register_global_middlewares(dp,
                                config,
                                # scheduler
                                )

    await on_startup(bot, config.tg_bot.admin_ids)

    try:
        await bot.delete_webhook(drop_pending_updates=False)
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()
        await dispose_db(db_engine)
        await dp.storage.close()
        await dp.stop_polling()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.error("Бот был запущен!")
