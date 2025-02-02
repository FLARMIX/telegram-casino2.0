from aiogram.types import Message
from aiogram.filters import Command
from aiogram.utils.markdown import hlink

from handlers.init_router import router

from database.database import Database
from scripts.scripts import Scripts


@router.message(Command("add_item"))
async def add_item(message: Message):
    db = Database()
    scr = Scripts()
    user_id = message.from_user.id
    command, target_username, item = message.text.split()
    if db.get_user_stat(user_id, "is_admin"):

        target_id = db.get_user_id_by_tgusername(target_username)

        tg_username = db.get_user_stat(target_id, "tgusername")[1:]
        username = db.get_user_stat(target_id, "username")
        formated_username = hlink(f'{username}', f'https://t.me/{tg_username}')

        if not target_id:
            await message.answer(f"Пользователь с ником '{target_username}' не найден.",
                                 reply_to_message_id=message.message_id)
            return

        db.add_item_to_user(target_id, item)
        await message.answer(f"Итем '{item}' успешно добавлен к пользователю {formated_username}.",
                             reply_to_message_id=message.message_id, disable_web_page_preview=True)
