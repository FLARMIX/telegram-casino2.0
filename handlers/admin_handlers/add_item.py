from aiogram.types import Message
from aiogram.filters import Command
from aiogram.utils.markdown import hlink
from sqlalchemy.ext.asyncio import AsyncSession

from database.methods import (get_user_stat, get_user_by_tguserid, get_user_by_tgusername,
                              add_item_to_user, get_user_items)
from handlers.init_router import router


@router.message(Command("add_item"))
async def add_item(message: Message, session: AsyncSession):
    user = await get_user_by_tguserid(session, message.from_user.id)
    if len(message.text.split()) <= 3:
        target_username, item = message.text.split()[1:]
    else:
        target_username = message.text.split()[1]
        item = ' '.join(message.text.split()[2:])

    if user.is_admin:

        target = await get_user_by_tgusername(session, target_username)
        target_id = target.tguserid

        tg_username = await get_user_stat(session, target_id, "tgusername")
        tg_username = tg_username[1:]
        username = await get_user_stat(session, target_id, "username")
        formated_username = hlink(f'{username}', f'https://t.me/{tg_username}')

        if not target_id:
            await message.answer(f"Пользователь с ником '{target_username}' не найден.",
                                 reply_to_message_id=message.message_id)
            return

        await add_item_to_user(session, target_id, item)
        user_items = await get_user_items(session, target_id)
        await message.answer(f"Предмет '{item}' успешно добавлен к пользователю {formated_username}. "
                             f"Теперь у него {user_items.get(item, 0)} предметов '{item}'.",
                             reply_to_message_id=message.message_id, disable_web_page_preview=True)
