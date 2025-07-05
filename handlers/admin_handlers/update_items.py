from aiogram.types import Message
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession

from database.methods import get_user_by_tguserid, update_items
from handlers.init_router import router

from json import loads


@router.message(Command('update_items'))
async def update_items_cmd(message: Message, session: AsyncSession):
    user = await get_user_by_tguserid(session, message.from_user.id)
    if user.is_admin:
        with open("handlers/admin_handlers/items.json", 'r', encoding='utf-8') as json_data:
            data = loads(json_data.read())
        await update_items(session, data)
        await message.answer("Updating items...")
