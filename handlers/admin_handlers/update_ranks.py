from aiogram.types import Message
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession

from config import ADMIN_IDs
from database.methods import get_user_by_tguserid, update_ranks
from handlers.init_router import router

from json import loads

from scripts.loggers import log


@router.message(Command('aui'))
@log("Updating items... Stop this is a... LOG!")
async def update_items_cmd(message: Message, session: AsyncSession):
    user = await get_user_by_tguserid(session, message.from_user.id)

    if str(user.tguserid) in ADMIN_IDs and user.is_admin:
        with open("handlers/admin_handlers/ranks.json", 'r', encoding='utf-8') as json_data:
            data = loads(json_data.read())
        await update_ranks(session, data)
        await message.answer("Updating items...")
    elif user.is_admin:
        await message.answer(f"Команда доступна только для администрации.")
    else:
        return
