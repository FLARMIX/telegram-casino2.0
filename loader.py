import logging
from json import loads

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio

from database.SQLmodels import User

import config
from database.methods import init_db, update_items, update_ranks
from database.session import AsyncSessionLocal
from handlers.init_router import router
from console.console import ConsoleManager
from middleware.database_session import DBSessionMiddleware
from scripts.media_cache import preload_media_cache


# (1, 'суперБабка', 1548320000, 0, '2025-06-28 01:34:14', '1970-01-01 00:00:00', 0, 2, 'None', 'None', 0, 1, 0, 'None', '@FLARMIX', 1438395869)
async def auto_calculate_payouts(user: User):
    await db.init_db()
    while True: # TODO Логика пополнения копилки рабства будет тут
        if user.your_slave != "None":
            await db.calculate_payout(user.your_slave)

async def user_cycle():
    users = await db.get_all_users()
    for user in users:
        asyncio.create_task(auto_calculate_payouts(user, db))


async def main_run():
    preload_media_cache()
    await init_db()

    logger = logging.getLogger(__name__)
    bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode='HTML'))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    dp.message.middleware(DBSessionMiddleware())
    dp.callback_query.middleware(DBSessionMiddleware())
    dp.update.middleware(DBSessionMiddleware())

    dp["bot"] = bot
    dp["logger"] = logger

    session = AsyncSessionLocal()

    with open('handlers/admin_handlers/items.json', 'r', encoding='utf-8') as json_data:
        data = loads(json_data.read())
        await update_items(session, data)

    with open('handlers/admin_handlers/ranks.json', 'r', encoding='utf-8') as json_data:
        data = loads(json_data.read())
        await update_ranks(session, data)

    console = ConsoleManager(session, logger, bot)
    asyncio.create_task(console.start_console())

    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await session.close()
