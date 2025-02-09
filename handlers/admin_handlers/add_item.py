from aiogram.types import Message
from aiogram.filters import Command
from aiogram.utils.markdown import hlink

from handlers.init_router import router

from database.database import Database


@router.message(Command("add_item"))
async def add_item(message: Message):
    db = Database()

    user_id = message.from_user.id
    if len(message.text.split()) <= 3:
        target_username, item = message.text.split()[1:]
    else:
        target_username = message.text.split()[1]
        item = ' '.join(message.text.split()[2:])
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
        user_items = db.get_user_items(target_id)
        await message.answer(f"Предмет '{item}' успешно добавлен к пользователю {formated_username}. "
                             f"Теперь у него {user_items.get(item, 0)} предметов '{item}'.",
                             reply_to_message_id=message.message_id, disable_web_page_preview=True)
