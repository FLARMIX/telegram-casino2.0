from aiogram.types import Message
from aiogram.filters import Command

from handlers.init_router import router

from database.database import Database

from json import loads


@router.message(Command('update_items'))
async def update_items(message: Message):
    db = Database()
    user_id = message.from_user.id
    if db.get_user_stat(user_id, "is_admin"):
        with open("handlers/admin_handlers/items.json", 'r', encoding='utf-8') as json_data:
            data = loads(json_data.read())
        db.update_items(data)
        await message.answer("Updating items...")
