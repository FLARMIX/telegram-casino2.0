from aiogram import F
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from database.methods import get_user_by_tguserid, get_item_by_name, get_dict_user_items, update_avatar, get_existing_items_names

from handlers.init_router import router

from scripts.loggers import log


@router.message(F.text.lower().startswith(("ава", "аватар", "avatar", "/ава", "/avatar")))
@log("Oh, you changing avatar? It's safe?")
async def change_avatar(message: Message, session: AsyncSession) -> None:
    user = await get_user_by_tguserid(session, message.from_user.id)
    message_text = message.text.split()
    message_len = len(message_text)

    items_names = await get_existing_items_names(session)
    items_map = {name.lower(): name for name in items_names}

    user_items = await get_dict_user_items(session, user.tguserid)

    if not user_items:
        await message.answer("У вас нет предметов.")
        return

    if message_len >= 2:
        user_input = ' '.join(message_text[1:]).strip().lower()

        if user_input not in items_map:
            await message.answer("Такого предмета нет!")
            return

        item_name = items_map[user_input]

        user_items = await get_dict_user_items(session, user.tguserid)
        if item_name not in user_items:
            await message.answer("У вас нет этого предмета!")
            return

        await update_avatar(session, user.tguserid, item_name)
        await message.answer(f"Вы успешно установили предмет {item_name}")
        return

    elif message_len == 1:
        await update_avatar(session, user.tguserid, 'черви')
        await message.answer("Установлен предмет по умолчанию.")
        return

